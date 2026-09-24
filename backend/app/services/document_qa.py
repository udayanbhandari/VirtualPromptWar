"""
Document Q&A service for ClauseWise.
Chat scoped strictly to the uploaded document + statute grounding — not a general chatbot.
"""

from __future__ import annotations

import random
import re
from typing import Any, Optional

from app.models.schemas import AskResponse, ChatMessage, Clause
from app.services.document_store import document_store
from app.services.gemini_client import gemini_client
from app.services.vector_store import retrieve_relevant_law

# Dynamic phrasing pool for concluding disclaimer
DISCLAIMER_VARIANTS = [
    "Note: This analysis is provided for legal informational purposes only and does not constitute formal legal counsel.",
    "Disclaimer: This summary reflects the textual provisions of your contract and statutory context, not tailored legal advice.",
    "Please note: This information is intended for educational clarity and should not substitute for professional legal advice.",
    "Important: The above highlights are generated from document text and statutes for informational reference, not legal representation.",
    "Notice: This explanation is for contractual assessment only and does not constitute a formal legal opinion.",
    "Informational notice: While grounded in your document and relevant law, this review is not licensed legal advice.",
]


class DocumentQA:
    """Orchestrates grounded Q&A answering strictly over document clauses and Indian statutes."""

    async def ask(
        self,
        doc_id: str,
        question: str,
        history: Optional[list[ChatMessage]] = None,
    ) -> AskResponse:
        doc = document_store.get(doc_id)
        if not doc:
            raise ValueError(f"Document with ID '{doc_id}' not found.")

        # Ensure document clauses are extracted
        clauses = doc.clauses
        if not clauses and doc.raw_text:
            clauses = await gemini_client.extract_clauses_from_text(doc.raw_text)
            doc = document_store.update_clauses(doc_id, clauses)
            clauses = doc.clauses if doc else []

        # Keep only the last 5 turns of conversation context
        recent_history = (history or [])[-5:]

        # Run retrieve_relevant_law() on the user's question
        statute_matches = await retrieve_relevant_law(question, top_k=3)

        # Filter statutes that are genuinely relevant (e.g. similarity >= 0.40 or top matching)
        statute_context_lines: list[str] = []
        relevant_citations: list[str] = []
        for match in statute_matches:
            # Include if similarity is meaningful
            if match.get("similarity", 0.0) >= 0.35:
                statute_context_lines.append(
                    f"[{match['citation']}] ({match['title']}): {match['text']}"
                )
                relevant_citations.append(match["citation"])

        statute_context = "\n\n".join(statute_context_lines)

        # If Gemini is configured and accessible, call Gemini
        if gemini_client.is_configured:
            try:
                return await self._ask_with_gemini(
                    question=question,
                    clauses=clauses,
                    statute_context=statute_context,
                    statute_matches=statute_matches,
                    history=recent_history,
                )
            except Exception as e:
                print(f"[DocumentQA] Gemini API call failed: {e}. Using deterministic grounded fallback.")

        return self._grounded_fallback_answer(
            question=question,
            clauses=clauses,
            statute_matches=statute_matches,
            history=recent_history,
        )

    async def _ask_with_gemini(
        self,
        question: str,
        clauses: list[Clause],
        statute_context: str,
        statute_matches: list[dict[str, Any]],
        history: list[ChatMessage],
    ) -> AskResponse:
        from google.genai import types

        clauses_context = "\n\n".join(
            f"Clause ID: {c.id}\nCategory: {c.category.value}\nVerbatim Text: \"{c.text}\"\nPlain Summary: {c.plain_language}"
            for c in clauses
        )

        system_instruction = (
            "You are ClauseWise Legal Q&A Assistant, an AI assistant strictly scoped to analyzing the user's uploaded legal document. "
            "You are NOT a general chatbot. You must adhere to the following strict boundaries:\n\n"
            "1. BOUNDED SCOPE: Answer the user's question ONLY using:\n"
            "   (a) The document's clauses provided in DOCUMENT CLAUSES. Always quote or cite the specific Clause ID (e.g., [clause-1]) "
            "that backs your answer.\n"
            "   (b) The statutory excerpts provided in RELEVANT STATUTES, when legally relevant to the question.\n"
            "2. OUT OF SCOPE: If the question asks about facts, topics, or issues that fall outside the provided document's scope "
            "and are not addressed by any clause in the contract (e.g. general trivia, unrelated laws, or topics not mentioned), "
            "you MUST explicitly say: \"This document doesn't address that.\" Never speculate, hallucinate, or fabricate an answer.\n"
            "3. NO CERTAINTY: Use balanced legal language; never state terms are definitively void without framing as 'may warrant review under...'.\n"
            "4. DISCLAIMER: End your answer with a short, natural framing statement reminding the user that this is informational and not legal advice. "
            "Vary your phrasing naturally each time."
        )

        history_context = ""
        if history:
            history_context = "CONVERSATION HISTORY (Last turns):\n" + "\n".join(
                f"{m.role.upper()}: {m.content}" for m in history
            ) + "\n\n"

        prompt = (
            f"{history_context}"
            f"DOCUMENT CLAUSES:\n{clauses_context}\n\n"
            f"RELEVANT STATUTES (Indian Law RAG):\n{statute_context or 'No closely matching statutory chunks found.'}\n\n"
            f"USER QUESTION: {question}\n\n"
            "Provide your grounded answer strictly following the instructions above."
        )

        response = gemini_client._genai_client.models.generate_content(
            model="gemini-2.5-flash",
            contents=prompt,
            config=types.GenerateContentConfig(
                system_instruction=system_instruction,
                temperature=0.2,
            ),
        )

        answer_text = (response.text or "").strip()

        # Extract referenced clause IDs
        referenced_ids = [c.id for c in clauses if c.id in answer_text]
        cited_statutes = [
            m["citation"]
            for m in statute_matches
            if m["citation"] in answer_text or m.get("section", "") in answer_text
        ]

        return AskResponse(
            answer=answer_text,
            sourceClauseIds=referenced_ids,
            relevantStatutes=cited_statutes,
        )

    def _grounded_fallback_answer(
        self,
        question: str,
        clauses: list[Clause],
        statute_matches: list[dict[str, Any]],
        history: list[ChatMessage],
    ) -> AskResponse:
        """
        Deterministic, strictly grounded fallback when LLM is in mock mode or unreachable.
        Handles three core cases:
        1. Answerable from document clauses.
        2. Requiring statute grounding.
        3. Outside document scope -> explicitly replies "This document doesn't address that."
        """
        q_lower = question.lower()
        disclaimer = random.choice(DISCLAIMER_VARIANTS)

        # Check for conversational follow-ups (e.g. "What about termination?")
        combined_q = q_lower
        if len(q_lower.split()) < 5 and history:
            last_turn = history[-1].content.lower()
            combined_q = f"{last_turn} {q_lower}"

        # 1. OUT OF SCOPE DETECTION
        # Check if the question asks about completely unrelated domains (cooking, weather, cricket, history, general trivia)
        out_of_scope_keywords = [
            "recipe", "cook", "capital of", "weather", "president", "cricket", "football",
            "movie", "song", "who is", "solar system", "planet", "math", "joke", "poem",
            "stock price", "crypto", "bitcoin", "tax return", "gst filing"
        ]
        if any(w in q_lower for w in out_of_scope_keywords):
            return AskResponse(
                answer=f"This document doesn't address that. The provided contract does not contain any provisions relating to your query.\n\n{disclaimer}",
                sourceClauseIds=[],
                relevantStatutes=[],
            )

        # 2. MATCH AGAINST DOCUMENT CLAUSES
        matched_clauses: list[Clause] = []
        for c in clauses:
            c_text_lower = c.text.lower()
            c_cat = c.category.value.lower()

            # Direct topic matching
            if "payment" in combined_q or "pay" in combined_q or "fee" in combined_q or "invoice" in combined_q or "interest" in combined_q or "net 15" in combined_q or "net 60" in combined_q:
                if c.category.value == "payment" or "payment" in c_text_lower:
                    matched_clauses.append(c)
            elif "terminat" in combined_q or "cancel" in combined_q or "notice" in combined_q or "cure period" in combined_q:
                if c.category.value == "termination" or "terminat" in c_text_lower:
                    matched_clauses.append(c)
            elif "liab" in combined_q or "damage" in combined_q or "cap" in combined_q:
                if c.category.value == "liability" or "liab" in c_text_lower:
                    matched_clauses.append(c)
            elif "indemn" in combined_q or "harmless" in combined_q:
                if c.category.value == "indemnity" or "indemn" in c_text_lower:
                    matched_clauses.append(c)
            elif "arbitrat" in combined_q or "dispute" in combined_q or "court" in combined_q or "jurisdiction" in combined_q or "venue" in combined_q or "law" in combined_q:
                if c.category.value == "arbitration" or "arbitrat" in c_text_lower:
                    matched_clauses.append(c)
            elif "compete" in combined_q or "non-compete" in combined_q or "restraint" in combined_q or "competitor" in combined_q or "freedom" in combined_q:
                if "compete" in c_text_lower or "independent" in c_text_lower:
                    matched_clauses.append(c)
            elif "intellectual property" in combined_q or "ip" in combined_q or "deliverable" in combined_q or "source code" in combined_q:
                if "intellectual property" in c_text_lower or "deliverable" in c_text_lower or "source code" in c_text_lower:
                    matched_clauses.append(c)
            elif "confidential" in combined_q or "proprietary" in combined_q or "secret" in combined_q:
                if c.category.value == "confidentiality" or "confidential" in c_text_lower:
                    matched_clauses.append(c)
            elif "rent" in combined_q or "deposit" in combined_q:
                if "rent" in c_text_lower or "deposit" in c_text_lower:
                    matched_clauses.append(c)

        # 3. STATUTE RELEVANCE CHECK
        # Does the question specifically ask about legality, enforceable law, statute, or Indian Contract Act?
        statute_requested = any(
            w in q_lower
            for w in [
                "legal", "law", "statute", "enforce", "act", "section", "valid", "void", "court",
                "penalt", "restraint", "rights under", "indian law", "allowed under"
            ]
        )

        top_statute = statute_matches[0] if statute_matches and statute_matches[0].get("similarity", 0) >= 0.35 else None

        # If no clause matched and question isn't purely a statute query
        if not matched_clauses:
            if statute_requested and top_statute:
                # Question is purely about legal statute context
                return AskResponse(
                    answer=(
                        f"While this specific document does not contain an explicit clause on this topic, under {top_statute['citation']} "
                        f"({top_statute['title']}): \"{top_statute['text']}\"\n\n"
                        f"{disclaimer}"
                    ),
                    sourceClauseIds=[],
                    relevantStatutes=[top_statute["citation"]],
                )
            return AskResponse(
                answer=f"This document doesn't address that. The contract text does not contain provisions covering this subject.\n\n{disclaimer}",
                sourceClauseIds=[],
                relevantStatutes=[],
            )

        # Deduplicate matched clauses
        matched_clauses = list({c.id: c for c in matched_clauses}.values())

        # Construct grounded answer
        primary_clause = matched_clauses[0]
        clause_citations = ", ".join(f"[{c.id}]" for c in matched_clauses)
        
        answer_parts: list[str] = []
        answer_parts.append(
            f"According to {clause_citations}, the document specifies:\n"
            f"\"{primary_clause.text}\"\n\n"
            f"In plain terms: {primary_clause.plain_language}"
        )

        if len(matched_clauses) > 1:
            second_clause = matched_clauses[1]
            answer_parts.append(
                f"\nAdditionally, [{second_clause.id}] provides: \"{second_clause.text}\""
            )

        # Include statute grounding if relevant
        relevant_statutes_list: list[str] = []
        if top_statute and (statute_requested or primary_clause.risk_level.value in ["high", "medium"]):
            relevant_statutes_list.append(top_statute["citation"])
            answer_parts.append(
                f"\n\nStatutory Context: Under {top_statute['citation']} ({top_statute['title']}), "
                f"{top_statute['text']}"
            )

        answer_parts.append(f"\n\n{disclaimer}")
        full_answer = "".join(answer_parts)

        return AskResponse(
            answer=full_answer,
            sourceClauseIds=[c.id for c in matched_clauses],
            relevantStatutes=relevant_statutes_list,
        )


document_qa = DocumentQA()
