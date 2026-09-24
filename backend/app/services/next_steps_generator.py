"""
Next Steps service for ClauseWise.
Turns flagged contract risks (MEDIUM/HIGH) into:
(a) an action checklist of concrete, non-legal-advice user actions
(b) a 'questions for your lawyer' brief to read aloud in consultations
(c) a 3-5 bullet executive document brief ready for print or export.
"""

from __future__ import annotations

import json
from typing import Any, Optional
from pydantic import BaseModel, Field

from app.models.schemas import (
    Clause,
    ClauseNextSteps,
    NextStep,
    NextStepsResponse,
    RiskLevel,
)
from app.services.document_store import document_store
from app.services.gemini_client import gemini_client


class GeminiNextStepsOutput(BaseModel):
    document_brief: list[str] = Field(
        description="3-5 concise bullet points summarizing key negotiation and legal exposure areas across the document"
    )
    flagged_clauses: list[ClauseNextSteps] = Field(
        description="Action checklists and consultation questions for each flagged clause"
    )


class NextStepsGenerator:
    """Generates structured action items, lawyer consultation questions, and document briefs."""

    async def generate_next_steps(self, doc_id: str) -> NextStepsResponse:
        doc = document_store.get(doc_id)
        if not doc:
            raise ValueError(f"Document with ID '{doc_id}' not found.")

        # Ensure clauses are extracted
        clauses = doc.clauses
        if not clauses and doc.raw_text:
            clauses = await gemini_client.extract_clauses_from_text(doc.raw_text)
            doc = document_store.update_clauses(doc_id, clauses)
            clauses = doc.clauses if doc else []

        # Filter for MEDIUM and HIGH risk clauses
        flagged = [
            c for c in clauses
            if c.risk_level in [RiskLevel.MEDIUM, RiskLevel.HIGH, RiskLevel.CRITICAL]
        ]

        # If Gemini is configured, use LLM generation
        if gemini_client.is_configured and flagged:
            try:
                return await self._generate_with_gemini(doc_id, flagged, clauses)
            except Exception as e:
                print(f"[NextStepsGenerator] Gemini call failed ({e}). Falling back to deterministic generator.")

        return self._heuristic_generate_next_steps(doc_id, flagged, clauses)

    async def _generate_with_gemini(
        self,
        doc_id: str,
        flagged: list[Clause],
        all_clauses: list[Clause],
    ) -> NextStepsResponse:
        from google.genai import types

        flagged_summary = "\n\n".join(
            f"Clause ID: {c.id}\nCategory: {c.category.value}\nRisk Level: {c.risk_level.value}\n"
            f"Verbatim Text: \"{c.text}\"\nPlain Summary: {c.plain_language}\nRisk Reason: {c.risk_reason}"
            for c in flagged
        )

        system_instruction = (
            "You are ClauseWise Next Steps & Consultation Generator. "
            "Your objective is to turn flagged legal contract risks into: "
            "(a) an actionChecklist: 2-4 short, concrete, practical actions the user could personally take "
            "(e.g., 'confirm notice duration in writing', 'request an invoice grace period', 'ask if cap can be lowered'). "
            "DO NOT give formal legal advice or say 'you should sue'. "
            "(b) lawyerQuestions: 1-3 specific, polite questions the user could literally read aloud in a legal consultation, "
            "directly referencing the clause. "
            "(c) documentBrief: 3-5 calm, executive bullet points summarizing the primary contractual exposure areas, "
            "formatted for printing or exporting before meeting counsel. "
            "Maintain a practical, calm, constructive tone — never alarmist."
        )

        prompt = (
            f"Document ID: {doc_id}\n\n"
            f"FLAGGED HIGH/MEDIUM RISK CLAUSES ({len(flagged)}):\n"
            f"{flagged_summary}\n\n"
            "Generate the structured consultation brief and action items."
        )

        config = types.GenerateContentConfig(
            system_instruction=system_instruction,
            response_mime_type="application/json",
            response_schema=GeminiNextStepsOutput,
            temperature=0.2,
        )

        response = gemini_client._genai_client.models.generate_content(
            model="gemini-2.5-flash",
            contents=prompt,
            config=config,
        )

        data = json.loads(response.text or "{}")
        output = GeminiNextStepsOutput.model_validate(data)

        # Build backward-compatible steps
        compat_steps: list[NextStep] = []
        for fc in output.flagged_clauses:
            first_action = fc.action_checklist[0] if fc.action_checklist else f"Review {fc.category} terms"
            compat_steps.append(
                NextStep(
                    title=f"Address {fc.category.replace('_', ' ').title()} Clause ({fc.clause_id})",
                    description=f"{first_action}. Lawyer query: '{fc.lawyer_questions[0] if fc.lawyer_questions else 'Review enforceability.'}'",
                    priority=fc.risk_level,
                )
            )

        return NextStepsResponse(
            docId=doc_id,
            documentBrief=output.document_brief,
            flaggedClauses=output.flagged_clauses,
            steps=compat_steps,
        )

    def _heuristic_generate_next_steps(
        self,
        doc_id: str,
        flagged: list[Clause],
        all_clauses: list[Clause],
    ) -> NextStepsResponse:
        """
        Deterministic generator producing calm, practical checklists and lawyer questions.
        """
        flagged_items: list[ClauseNextSteps] = []
        compat_steps: list[NextStep] = []

        for c in flagged:
            actions: list[str] = []
            lawyer_qs: list[str] = []
            cat = c.category.value
            txt_lower = c.text.lower()

            if cat == "arbitration" or ("arbitrat" in txt_lower and "pay" not in txt_lower):
                actions = [
                    "Inquire whether dispute arbitration can be conducted virtually or moved to a local city.",
                    "Request that English law / foreign venue be replaced with Indian law or mutual home jurisdiction.",
                ]
                lawyer_qs = [
                    f"In {c.id}, what are the practical cost and filing fee implications of requiring arbitration in a foreign forum?",
                    f"Is clause {c.id}'s waiver of local court jurisdiction valid under Section 28 of the Indian Contract Act?",
                ]
            elif cat == "termination" or ("terminat" in txt_lower and "month" not in txt_lower and "non-compete" not in txt_lower):
                actions = [
                    "Ask the counterparty if a mutual 30-day written notice period can be inserted.",
                    "Request a standard 15-day cure period for any alleged performance deficiencies.",
                    "Verify that work completed prior to termination is unconditionally payable.",
                ]
                lawyer_qs = [
                    f"Does clause {c.id}'s immediate termination right create a risk of wrongful repudiation under Section 39?",
                    f"How can we redraft clause {c.id} to ensure all in-progress milestone billings are preserved upon termination?",
                ]
            elif "compete" in txt_lower or "restraint" in txt_lower:
                actions = [
                    "Ask the counterparty to narrow any post-contractual non-compete to direct solicitation only.",
                    "Request specific geographical and industry exceptions for your primary freelance practice.",
                ]
                lawyer_qs = [
                    f"Given Section 27 of the Indian Contract Act, is the worldwide 24-month non-compete in {c.id} legally enforceable against an independent contractor?",
                    f"Could signing clause {c.id} affect my ability to accept engagements from other clients in the tech sector?",
                ]
            elif "intellectual property" in txt_lower or "source code" in txt_lower or "deliverables" in txt_lower:
                actions = [
                    "Propose that IP assignments occur only upon full and final payment of all milestone invoices.",
                    "Retain ownership of pre-existing background technology and open-source tooling.",
                ]
                lawyer_qs = [
                    f"Under clause {c.id}, does transferring IP prior to payment compromise our ability to recover unpaid invoices?",
                    f"What conditional assignment clause should we introduce to safeguard our work product?",
                ]
            elif cat == "payment" or "invoice" in txt_lower or "pay" in txt_lower:
                actions = [
                    "Request counterparty to clarify whether invoice payment cycles can be shortened to Net 30 or Net 15.",
                    "Ask in writing if late payment interest charges or penalties can be waived or reduced.",
                    "Maintain documented timesheets and delivery milestone receipts for every submission.",
                ]
                lawyer_qs = [
                    f"In {c.id}, is the withholding mechanism permissible without formal audit or dispute notice?",
                    f"Under the Indian Contract Act or applicable commercial law, does clause {c.id}'s payment timeline leave adequate remedies for non-payment?",
                ]
            elif cat in ["liability", "indemnity"] or "liab" in txt_lower or "indemn" in txt_lower:
                actions = [
                    "Propose a mutual liability ceiling capped at 100% of fees actually received under the contract.",
                    "Request the exclusion of indirect, special, and consequential damages.",
                    "Ensure indemnity is limited to direct damages caused solely by proven gross negligence.",
                ]
                lawyer_qs = [
                    f"Clause {c.id} appears uncapped. Is an unlimited indemnity standard in this industry, and what exposure does it create?",
                    f"Can we replace clause {c.id} with a standard bilateral liability cap tied to fees paid?",
                ]
            elif cat == "confidentiality" or "confidential" in txt_lower or "secret" in txt_lower or "perpetual" in txt_lower:
                actions = [
                    "Propose capping the confidentiality survival term at 2 to 3 years following contract termination.",
                    "Request a standard carve-out for information already in the public domain or independently developed.",
                ]
                lawyer_qs = [
                    f"Does the perpetual confidentiality requirement in {c.id} create ongoing exposure after our engagement ends?",
                    f"How can we narrow clause {c.id} to protect standard commercial know-how?",
                ]
            else:
                actions = [
                    f"Highlight clause {c.id} to the counterparty and request clarification on its operational scope.",
                    "Document mutual expectations regarding performance standards in an email or annexure.",
                ]
                lawyer_qs = [
                    f"Regarding clause {c.id}, how do courts typically interpret this wording in commercial agreements?",
                    f"What amendment would you recommend to clause {c.id} to balance our risk?",
                ]

            flagged_items.append(
                ClauseNextSteps(
                    clauseId=c.id,
                    category=c.category.value,
                    riskLevel=c.risk_level,
                    clauseText=c.text,
                    plainLanguage=c.plain_language,
                    actionChecklist=actions[:3],
                    lawyerQuestions=lawyer_qs[:2],
                )
            )

            compat_steps.append(
                NextStep(
                    title=f"Address {c.category.value.replace('_', ' ').title()} Clause ({c.id})",
                    description=f"{actions[0]} Consultation question: '{lawyer_qs[0]}'",
                    priority=c.risk_level,
                )
            )

        # Overall Document Brief (3-5 bullets)
        document_brief = [
            f"Identified {len(flagged)} clause(s) with elevated contractual exposure requiring focused negotiation.",
            "Primary areas of concern include asymmetrical liability provisions, potential non-payment mechanisms, and unilateral termination terms.",
            "Review recommended revisions to ensure bilateral parity, capped liabilities, and clear milestone acceptance criteria.",
            "Clarify dispute jurisdiction and dispute resolution fee allocation to avoid burdensome foreign forum expenses.",
            "Bring this brief and the flagged clause action checklist to your legal consultation for targeted contract review.",
        ]

        return NextStepsResponse(
            docId=doc_id,
            documentBrief=document_brief,
            flaggedClauses=flagged_items,
            steps=compat_steps,
        )


next_steps_generator = NextStepsGenerator()
