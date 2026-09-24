"""
Pydantic schemas for ClauseWise.

These are the shared contracts between frontend and backend.
Every route request/response is typed here.
"""

from __future__ import annotations

import uuid
from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field, field_validator


# ── Core domain models ──────────────────────────────────────────────


class RiskLevel(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class ClauseCategory(str, Enum):
    PAYMENT = "payment"
    TERMINATION = "termination"
    LIABILITY = "liability"
    INDEMNITY = "indemnity"
    AUTO_RENEWAL = "auto_renewal"
    ARBITRATION = "arbitration"
    CONFIDENTIALITY = "confidentiality"
    OTHER = "other"


class Clause(BaseModel):
    """A single contractual clause extracted from a document."""

    id: str = Field(default_factory=lambda: f"clause-{uuid.uuid4().hex[:6]}")
    text: str = Field(description="Verbatim text of the clause as found in the agreement")
    category: ClauseCategory = Field(default=ClauseCategory.OTHER)
    plain_language: str = Field(
        alias="plainLanguage",
        default="",
        description="1-2 sentence rewrite of the clause in simple, plain English",
    )
    risk_level: RiskLevel = Field(alias="riskLevel", default=RiskLevel.LOW)
    risk_reason: str = Field(
        alias="riskReason",
        default="",
        description="1 sentence explaining the risk, phrased as 'may warrant review because...'",
    )
    conflicts_with: list[str] = Field(
        alias="conflictsWith",
        default_factory=list,
        description="List of other clause IDs in this document that directly contradict or conflict with this clause",
    )

    model_config = {"populate_by_name": True}

    @field_validator("category", mode="before")
    @classmethod
    def _normalize_category_val(cls, v):
        if isinstance(v, ClauseCategory):
            return v
        if isinstance(v, str):
            cleaned = v.strip().lower().replace(" ", "_").replace("-", "_")
            for member in ClauseCategory:
                if member.value == cleaned:
                    return member
        return ClauseCategory.OTHER

    @field_validator("risk_level", mode="before")
    @classmethod
    def _normalize_risk_val(cls, v):
        if isinstance(v, RiskLevel):
            return v
        if isinstance(v, str):
            cleaned = v.strip().lower()
            if "high" in cleaned or "critical" in cleaned:
                return RiskLevel.HIGH
            elif "med" in cleaned:
                return RiskLevel.MEDIUM
            return RiskLevel.LOW
        return RiskLevel.LOW


class DocumentSummary(BaseModel):
    """Summary produced after ingesting a legal document."""

    doc_id: str = Field(alias="docId", default_factory=lambda: str(uuid.uuid4()))
    file_name: str = Field(alias="fileName")
    plain_summary: str = Field(alias="plainSummary", default="")
    clauses: list[Clause] = Field(default_factory=list)

    model_config = {"populate_by_name": True}


# ── Ingest ───────────────────────────────────────────────────────────


class IngestRequest(BaseModel):
    """Metadata for ingestion request."""

    file_name: str = Field(alias="fileName", default="document.pdf")

    model_config = {"populate_by_name": True}


class IngestResponse(BaseModel):
    """Returned after a document is ingested via multimodal Gemini."""

    doc_id: str = Field(alias="docId")
    file_name: str = Field(alias="fileName")
    raw_text: str = Field(alias="rawText")
    file_path: Optional[str] = Field(alias="filePath", default=None)
    mime_type: str = Field(alias="mimeType", default="application/pdf")
    document: Optional[DocumentSummary] = None

    model_config = {"populate_by_name": True}


# ── Clauses ──────────────────────────────────────────────────────────


class ClausesResponse(BaseModel):
    """Returned when listing or extracting clauses for a document."""

    doc_id: str = Field(alias="docId")
    clauses: list[Clause]

    model_config = {"populate_by_name": True}


# ── Compare (Phase 3 Structured Diff) ────────────────────────────────


class FavorsParty(str, Enum):
    DOC_A = "docA"
    DOC_B = "docB"
    NEUTRAL = "neutral"


class ClauseDiffItem(BaseModel):
    """A paired comparison of clauses addressing the same topic across two documents."""

    topic: str
    doc_a_text: Optional[str] = Field(alias="docA_text", default=None)
    doc_b_text: Optional[str] = Field(alias="docB_text", default=None)
    difference_summary: str = Field(alias="difference_summary", default="")
    favors: FavorsParty = Field(default=FavorsParty.NEUTRAL)
    risk_delta: str = Field(
        alias="riskDelta",
        default="",
        description="Explains whether the change increases or decreases risk for the user, and why",
    )
    clause_a: Optional[Clause] = Field(alias="clauseA", default=None)
    clause_b: Optional[Clause] = Field(alias="clauseB", default=None)
    difference: Optional[str] = Field(default=None)

    model_config = {"populate_by_name": True}


class MissingClauseItem(BaseModel):
    """A clause present in one document but completely absent in the other."""

    clause_id: Optional[str] = Field(alias="clauseId", default=None)
    present_in: str = Field(alias="presentIn", description="'docA' or 'docB'")
    missing_from: str = Field(alias="missingFrom", description="'docB' or 'docA'")
    topic: str
    text: str
    impact: str = Field(description="Legal impact of this clause being omitted")

    model_config = {"populate_by_name": True}


class ComparisonResult(BaseModel):
    """Structured diff result between two documents."""

    doc_id_a: str = Field(alias="docIdA")
    doc_id_b: str = Field(alias="docIdB")
    overall_assessment: str = Field(
        alias="overallAssessment",
        description="Plain-language verdict on which contract is more favorable and benefits the user more",
    )
    overall_favors: FavorsParty = Field(
        alias="overallFavors",
        default=FavorsParty.NEUTRAL,
        description="Which document favors the user: docA, docB, or neutral",
    )
    pairs: list[ClauseDiffItem] = Field(
        alias="pairs",
        default_factory=list,
        description="Paired clauses addressing the same topic",
    )
    missing_clauses: list[MissingClauseItem] = Field(
        alias="missingClauses",
        default_factory=list,
        description="Clauses present in one document but missing from the other",
    )
    # Backward compatibility with Phase 0 list
    results: list[ClauseDiffItem] = Field(default_factory=list)

    model_config = {"populate_by_name": True}


class CompareRequest(BaseModel):
    """Request to compare two ingested documents."""

    doc_id_a: str = Field(alias="docIdA")
    doc_id_b: str = Field(alias="docIdB")

    model_config = {"populate_by_name": True}


class CompareResponse(BaseModel):
    """Result of comparing two documents."""

    comparison: ComparisonResult
    results: list[ClauseDiffItem] = Field(default_factory=list)

    model_config = {"populate_by_name": True}


# ── Ask (RAG Q&A) ───────────────────────────────────────────────────


class ChatMessage(BaseModel):
    """A message in the chat conversation history."""

    role: str = Field(description="'user' or 'assistant'")
    content: str

    model_config = {"populate_by_name": True}


class AskRequest(BaseModel):
    """Free-form question about an ingested document with conversational context."""

    doc_id: str = Field(alias="docId")
    question: str
    history: list[ChatMessage] = Field(
        default_factory=list,
        description="Conversation history turns (last 5 turns maintained)",
    )

    model_config = {"populate_by_name": True}


class AskResponse(BaseModel):
    """AI-generated answer with source clause references and relevant statutes."""

    answer: str
    source_clause_ids: list[str] = Field(
        alias="sourceClauseIds", default_factory=list
    )
    relevant_statutes: list[str] = Field(
        alias="relevantStatutes", default_factory=list
    )

    model_config = {"populate_by_name": True}


# ── Next Steps (Phase 5) ───────────────────────────────────────────


class ClauseNextSteps(BaseModel):
    """Action checklist and lawyer consultation questions for a single flagged clause."""

    clause_id: str = Field(alias="clauseId")
    category: str
    risk_level: RiskLevel = Field(alias="riskLevel")
    clause_text: str = Field(alias="clauseText")
    plain_language: str = Field(alias="plainLanguage")
    action_checklist: list[str] = Field(
        alias="actionChecklist",
        description="2-4 short, concrete, non-legal-advice actions the user could personally take",
    )
    lawyer_questions: list[str] = Field(
        alias="lawyerQuestions",
        description="1-3 specific questions the user could literally read aloud in a consultation",
    )

    model_config = {"populate_by_name": True}


class NextStep(BaseModel):
    """A recommended action for backward compatibility."""

    title: str
    description: str
    priority: RiskLevel = RiskLevel.MEDIUM


class NextStepsRequest(BaseModel):
    """Request recommended next steps for a document."""

    doc_id: str = Field(alias="docId")

    model_config = {"populate_by_name": True}


class NextStepsResponse(BaseModel):
    """AI-generated next steps, consultation questions, and document brief."""

    doc_id: str = Field(alias="docId")
    document_brief: list[str] = Field(
        alias="documentBrief",
        default_factory=list,
        description="3-5 bullet overall executive summary meant to be printed/exported before a legal consultation",
    )
    flagged_clauses: list[ClauseNextSteps] = Field(
        alias="flaggedClauses",
        default_factory=list,
        description="Action checklist and lawyer questions grouped by flagged clause",
    )
    steps: list[NextStep] = Field(
        default_factory=list,
        description="Backward compatible list of prioritized next steps",
    )

    model_config = {"populate_by_name": True}
