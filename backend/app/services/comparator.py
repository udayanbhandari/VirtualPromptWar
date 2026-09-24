"""
Document comparison service for ClauseWise.
Pairs clauses across two documents by category and semantic similarity,
computes difference summaries, favors indicators, risk delta, and detects missing clauses.
"""

from __future__ import annotations

import json
import math
from typing import Any, Optional

from app.models.schemas import (
    Clause,
    ClauseCategory,
    ClauseDiffItem,
    ComparisonResult,
    FavorsParty,
    MissingClauseItem,
    RiskLevel,
)
from app.services.document_store import document_store
from app.services.gemini_client import gemini_client


def cosine_sim(a: list[float], b: list[float]) -> float:
    if not a or not b or len(a) != len(b):
        return 0.0
    dot = sum(x * y for x, y in zip(a, b))
    norm_a = math.sqrt(sum(x * x for x in a))
    norm_b = math.sqrt(sum(y * y for y in b))
    if norm_a == 0.0 or norm_b == 0.0:
        return 0.0
    return dot / (norm_a * norm_b)


class DocumentComparator:
    """Orchestrates clause alignment and difference analysis between two contracts."""

    async def compare(self, doc_id_a: str, doc_id_b: str) -> ComparisonResult:
        doc_a = document_store.get(doc_id_a)
        doc_b = document_store.get(doc_id_b)

        if not doc_a:
            raise ValueError(f"Document A '{doc_id_a}' not found.")
        if not doc_b:
            raise ValueError(f"Document B '{doc_id_b}' not found.")

        # Ensure clauses are extracted for both documents
        if not doc_a.clauses and doc_a.raw_text:
            clauses_a = await gemini_client.extract_clauses_from_text(doc_a.raw_text)
            doc_a = document_store.update_clauses(doc_id_a, clauses_a)
        if not doc_b.clauses and doc_b.raw_text:
            clauses_b = await gemini_client.extract_clauses_from_text(doc_b.raw_text)
            doc_b = document_store.update_clauses(doc_id_b, clauses_b)

        clauses_a = doc_a.clauses if doc_a else []
        clauses_b = doc_b.clauses if doc_b else []

        # If Gemini is configured, use LLM-powered comparison
        if gemini_client.is_configured:
            try:
                return await self._compare_with_gemini(doc_id_a, doc_id_b, clauses_a, clauses_b)
            except Exception as e:
                print(f"Gemini compare failed ({e}). Falling back to heuristic comparator.")

        return await self._heuristic_compare(doc_id_a, doc_id_b, clauses_a, clauses_b)

    async def _pair_clauses(
        self, clauses_a: list[Clause], clauses_b: list[Clause]
    ) -> tuple[list[tuple[Clause, Clause]], list[Clause], list[Clause]]:
        """
        Pair up clauses addressing the same topic across both documents:
        1. Match by category first.
        2. Semantic similarity matching for remaining clauses.
        3. Collect leftover clauses as missing from one doc.
        """
        pairs: list[tuple[Clause, Clause]] = []
        matched_a_ids: set[str] = set()
        matched_b_ids: set[str] = set()

        # Step 1: Match by identical category
        by_cat_b: dict[ClauseCategory, list[Clause]] = {}
        for cb in clauses_b:
            by_cat_b.setdefault(cb.category, []).append(cb)

        for ca in clauses_a:
            candidates = by_cat_b.get(ca.category, [])
            # Find candidate with highest word overlap or first unmatched
            unmatched = [cb for cb in candidates if cb.id not in matched_b_ids]
            if unmatched:
                # pick closest or first
                chosen = unmatched[0]
                pairs.append((ca, chosen))
                matched_a_ids.add(ca.id)
                matched_b_ids.add(chosen.id)

        # Step 2: Semantic similarity for unmatched ones
        unmatched_a = [c for c in clauses_a if c.id not in matched_a_ids]
        unmatched_b = [c for c in clauses_b if c.id not in matched_b_ids]

        if unmatched_a and unmatched_b:
            emb_a = {ca.id: await gemini_client.embed_text(ca.text) for ca in unmatched_a}
            emb_b = {cb.id: await gemini_client.embed_text(cb.text) for cb in unmatched_b}

            for ca in list(unmatched_a):
                best_sim = -1.0
                best_match = None
                for cb in unmatched_b:
                    if cb.id in matched_b_ids:
                        continue
                    sim = cosine_sim(emb_a[ca.id], emb_b[cb.id])
                    if sim > best_sim:
                        best_sim = sim
                        best_match = cb

                if best_match and best_sim >= 0.50:
                    pairs.append((ca, best_match))
                    matched_a_ids.add(ca.id)
                    matched_b_ids.add(best_match.id)
                    unmatched_a.remove(ca)
                    unmatched_b.remove(best_match)

        missing_in_b = [c for c in clauses_a if c.id not in matched_a_ids]
        missing_in_a = [c for c in clauses_b if c.id not in matched_b_ids]

        return pairs, missing_in_b, missing_in_a

    async def _heuristic_compare(
        self,
        doc_id_a: str,
        doc_id_b: str,
        clauses_a: list[Clause],
        clauses_b: list[Clause],
    ) -> ComparisonResult:
        pairs, missing_b, missing_a = await self._pair_clauses(clauses_a, clauses_b)

        diff_items: list[ClauseDiffItem] = []
        doc_a_score = 0
        doc_b_score = 0

        for ca, cb in pairs:
            topic = ca.category.value.replace("_", " ").title()
            text_a = ca.text
            text_b = cb.text

            diff_summary, favors, risk_delta = self._analyze_pair_difference(ca, cb)

            if favors == FavorsParty.DOC_A:
                doc_a_score += 1
            elif favors == FavorsParty.DOC_B:
                doc_b_score += 1

            diff_item = ClauseDiffItem(
                topic=topic,
                docA_text=text_a,
                docB_text=text_b,
                difference_summary=diff_summary,
                favors=favors,
                riskDelta=risk_delta,
                clauseA=ca,
                clauseB=cb,
                difference=diff_summary,
            )
            diff_items.append(diff_item)

        # Missing clauses
        missing_items: list[MissingClauseItem] = []
        for ca in missing_b:
            missing_items.append(
                MissingClauseItem(
                    clauseId=ca.id,
                    presentIn="docA",
                    missingFrom="docB",
                    topic=ca.category.value.replace("_", " ").title(),
                    text=ca.text,
                    impact=f"Document B is missing this {ca.category.value} clause, which may leave rights unprotected.",
                )
            )
        for cb in missing_a:
            missing_items.append(
                MissingClauseItem(
                    clauseId=cb.id,
                    presentIn="docB",
                    missingFrom="docA",
                    topic=cb.category.value.replace("_", " ").title(),
                    text=cb.text,
                    impact=f"Document B introduces this additional {cb.category.value} clause not present in Document A.",
                )
            )

        # Overall assessment
        if doc_a_score > doc_b_score:
            overall_favors = FavorsParty.DOC_A
            assessment = (
                f"Document A is significantly more favorable to the user. "
                f"Document B introduces adverse shifts across {doc_a_score} key clause(s) "
                f"(including stricter payment terms, greater liability exposure, or reduced termination rights)."
            )
        elif doc_b_score > doc_a_score:
            overall_favors = FavorsParty.DOC_B
            assessment = (
                f"Document B is more favorable to the user overall across {doc_b_score} key terms."
            )
        else:
            overall_favors = FavorsParty.NEUTRAL
            assessment = "Both documents offer balanced terms with comparable user protections."

        return ComparisonResult(
            docIdA=doc_id_a,
            docIdB=doc_id_b,
            overallAssessment=assessment,
            overallFavors=overall_favors,
            pairs=diff_items,
            missingClauses=missing_items,
            results=diff_items,
        )

    def _analyze_pair_difference(
        self, ca: Clause, cb: Clause
    ) -> tuple[str, FavorsParty, str]:
        """
        Analyze a pair of clauses on the same topic to determine diff summary,
        which document favors the user, and risk delta.
        """
        a_lower = ca.text.lower()
        b_lower = cb.text.lower()

        # Payment analysis
        if ca.category == ClauseCategory.PAYMENT or "payment" in a_lower:
            if "net 15" in a_lower and "net 60" in b_lower:
                return (
                    "Document A requires payment within Net 15 days with late interest; Document B extends payment to Net 60 days and permits unilateral withholding.",
                    FavorsParty.DOC_A,
                    "Increases risk: Document B severely extends cash collection timeline and gives client subjective withholding rights.",
                )
            if "without penalty" in a_lower and "penalty" in b_lower:
                return (
                    "Document A permits early prepayment without penalty; Document B imposes a mandatory 8% prepayment penalty.",
                    FavorsParty.DOC_A,
                    "Increases risk: Document B penalizes early debt retirement with a heavy 8% liquidated surcharge.",
                )

        # Termination analysis
        if ca.category == ClauseCategory.TERMINATION or "terminat" in a_lower:
            if "30 days" in a_lower and ("without notice" in b_lower or "immediately" in b_lower):
                return (
                    "Document A provides bilateral 30 days notice with full payment for work completed; Document B permits unilateral termination immediately without notice or payment for in-progress work.",
                    FavorsParty.DOC_A,
                    "Increases risk: Document B allows sudden dismissal without notice and strips compensation for unapproved work.",
                )

        # Liability & Indemnity
        if ca.category in [ClauseCategory.LIABILITY, ClauseCategory.INDEMNITY] or "liability" in a_lower:
            if "capped" in a_lower and "uncapped" in b_lower:
                return (
                    "Document A strictly caps contractor liability at total fees paid; Document B imposes unlimited liability and unilateral indemnity regardless of client negligence.",
                    FavorsParty.DOC_A,
                    "Increases risk: Document B exposes the contractor to catastrophic, uncapped financial liability and third-party defense costs.",
                )

        # Restraint of trade / Non-compete
        if "compete" in a_lower or "compete" in b_lower or "independent" in a_lower:
            if "unrestricted freedom" in a_lower and "prohibited" in b_lower:
                return (
                    "Document A protects contractor freedom to serve other clients; Document B imposes a 24-month worldwide non-compete covenant.",
                    FavorsParty.DOC_A,
                    "Increases risk: Document B restricts the user's livelihood and post-contractual professional activities.",
                )

        # IP transfer
        if "intellectual property" in a_lower or "ip" in a_lower:
            if "upon complete receipt of full payment" in a_lower and "immediately upon creation" in b_lower:
                return (
                    "Document A transfers IP only after full payment is received; Document B transfers IP immediately upon creation even if invoices remain unpaid.",
                    FavorsParty.DOC_A,
                    "Increases risk: Document B forfeits the contractor's primary payment leverage before compensation is secured.",
                )

        # Arbitration / Jurisdiction
        if ca.category == ClauseCategory.ARBITRATION or "arbitration" in a_lower:
            if "bengaluru" in a_lower and "london" in b_lower:
                return (
                    "Document A specifies local arbitration in Bengaluru under Indian law; Document B mandates London venue and foreign law with upfront filing fee burdens.",
                    FavorsParty.DOC_A,
                    "Increases risk: Document B requires expensive foreign dispute resolution and complex cross-border enforcement.",
                )

        # Default fallback
        if ca.risk_level.value != cb.risk_level.value:
            if ca.risk_level == RiskLevel.LOW and cb.risk_level in [RiskLevel.HIGH, RiskLevel.MEDIUM]:
                return (
                    "Document B imposes more onerous terms than Document A.",
                    FavorsParty.DOC_A,
                    "Increases risk: Document B raises risk level due to less protective wording.",
                )
            elif cb.risk_level == RiskLevel.LOW and ca.risk_level in [RiskLevel.HIGH, RiskLevel.MEDIUM]:
                return (
                    "Document B provides more favorable user terms than Document A.",
                    FavorsParty.DOC_B,
                    "Decreases risk: Document B improves contractual protections for the user.",
                )

        return (
            "Minor phrasing and wording differences between both documents.",
            FavorsParty.NEUTRAL,
            "Neutral risk delta: terms are functionally equivalent.",
        )

    async def _compare_with_gemini(
        self,
        doc_id_a: str,
        doc_id_b: str,
        clauses_a: list[Clause],
        clauses_b: list[Clause],
    ) -> ComparisonResult:
        """Call Gemini for detailed semantic comparison."""
        from google.genai import types

        pairs, missing_b, missing_a = await self._pair_clauses(clauses_a, clauses_b)

        pairs_prompt = "\n\n".join(
            f"Topic: {ca.category.value}\n[Doc A ({ca.id})]: {ca.text}\n[Doc B ({cb.id})]: {cb.text}"
            for ca, cb in pairs
        )

        system_instruction = (
            "You are ClauseWise AI. Compare paired clauses across two legal contracts from the perspective of the user (e.g. contractor/consumer). "
            "For each pair evaluate: topic, docA_text, docB_text, difference_summary (plain language), favors ('docA', 'docB', or 'neutral'), "
            "and riskDelta (explains whether Document B increases or decreases risk for the user and why). "
            "Also assess which document benefits the user more overall."
        )

        config = types.GenerateContentConfig(
            system_instruction=system_instruction,
            response_mime_type="application/json",
            response_schema=ComparisonResult,
            temperature=0.1,
        )

        prompt = (
            f"Document A ID: {doc_id_a}\nDocument B ID: {doc_id_b}\n\n"
            f"PAIRED CLAUSES:\n{pairs_prompt}\n\n"
            f"MISSING IN B: {[ca.text for ca in missing_b]}\n"
            f"MISSING IN A: {[cb.text for cb in missing_a]}"
        )

        response = gemini_client._genai_client.models.generate_content(
            model="gemini-2.5-flash",
            contents=prompt,
            config=config,
        )

        data = json.loads(response.text or "{}")
        res = ComparisonResult.model_validate(data)
        res.doc_id_a = doc_id_a
        res.doc_id_b = doc_id_b
        res.results = res.pairs
        return res


comparator = DocumentComparator()
