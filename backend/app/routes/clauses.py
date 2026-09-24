"""
Clauses route - structured clause extraction, risk assessment, and conflict detection.
"""

from fastapi import APIRouter, HTTPException, Query

from app.models.schemas import ClausesResponse, RiskLevel
from app.services.document_store import document_store
from app.services.gemini_client import gemini_client

router = APIRouter(prefix="/clauses", tags=["clauses"])


@router.post("/{doc_id}", response_model=ClausesResponse)
async def extract_clauses(doc_id: str) -> ClausesResponse:
    """
    Extract structured clauses from an ingested document using Gemini.
    Categorizes clauses, rewrites into plain language, evaluates grounded risks,
    detects intra-document inconsistencies (conflictsWith), persists to record, and returns clauses.
    """
    doc = document_store.get(doc_id)
    if not doc:
        raise HTTPException(
            status_code=404,
            detail=f"Document with ID '{doc_id}' not found. Please upload it via /api/ingest/ first.",
        )

    if not doc.raw_text.strip():
        raise HTTPException(
            status_code=400,
            detail=f"Document '{doc_id}' has no extracted text to analyze.",
        )

    # Call Gemini structured output extraction
    try:
        clauses = await gemini_client.extract_clauses_from_text(doc.raw_text)
    except ValueError as ve:
        raise HTTPException(
            status_code=422,
            detail=str(ve),
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Clause extraction failed: {str(e)}. Please retry.",
        )

    # Persist clauses to document store record
    document_store.update_clauses(doc_id, clauses)

    return ClausesResponse(docId=doc_id, clauses=clauses)


@router.get("/{doc_id}", response_model=ClausesResponse)
async def get_clauses(
    doc_id: str,
    category: str | None = Query(None, description="Filter by clause category"),
    risk_level: RiskLevel | None = Query(
        None, alias="riskLevel", description="Filter by risk level"
    ),
) -> ClausesResponse:
    """
    Retrieve extracted clauses for a document.
    If clauses have not been extracted yet, triggers extraction automatically.
    """
    doc = document_store.get(doc_id)
    if not doc:
        raise HTTPException(
            status_code=404,
            detail=f"Document with ID '{doc_id}' not found.",
        )

    # If clauses haven't been extracted yet, extract and save
    if not doc.clauses and doc.raw_text:
        clauses = await gemini_client.extract_clauses_from_text(doc.raw_text)
        doc = document_store.update_clauses(doc_id, clauses)

    clauses = doc.clauses if doc else []

    # Apply filters if provided
    if category:
        clauses = [
            c for c in clauses if c.category.value.lower() == category.lower()
        ]
    if risk_level:
        clauses = [c for c in clauses if c.risk_level == risk_level]

    return ClausesResponse(docId=doc_id, clauses=clauses)
