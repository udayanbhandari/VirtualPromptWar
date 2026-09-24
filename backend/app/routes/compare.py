"""
Compare route - structured clause diff between two ingested documents.
"""

from fastapi import APIRouter, HTTPException

from app.models.schemas import CompareRequest, CompareResponse
from app.services.comparator import comparator
from app.services.document_store import document_store

router = APIRouter(prefix="/compare", tags=["compare"])


@router.post("/", response_model=CompareResponse)
async def compare_documents(body: CompareRequest) -> CompareResponse:
    """
    Compare two ingested documents:
    - Fetches clause sets for docIdA and docIdB.
    - Pairs clauses addressing the same topic (category match first, then semantic similarity).
    - Returns structured differences: topic, docA_text, docB_text, difference_summary,
      favors (docA | docB | neutral), and riskDelta.
    - Lists clauses present in one document but missing from the other.
    - Delivers an overall favorability assessment indicating which contract benefits the user more.
    """
    # Validate: doc IDs must be different
    if body.doc_id_a.strip() == body.doc_id_b.strip():
        raise HTTPException(
            status_code=400,
            detail="Cannot compare a document with itself. Please provide two different document IDs.",
        )

    # Validate: both documents must exist
    doc_a = document_store.get(body.doc_id_a)
    if not doc_a:
        raise HTTPException(
            status_code=404,
            detail=f"Document A '{body.doc_id_a}' not found. Please upload it via /api/ingest/ first.",
        )
    doc_b = document_store.get(body.doc_id_b)
    if not doc_b:
        raise HTTPException(
            status_code=404,
            detail=f"Document B '{body.doc_id_b}' not found. Please upload it via /api/ingest/ first.",
        )

    # Validate: both documents must have extracted clauses
    if not doc_a.clauses:
        raise HTTPException(
            status_code=400,
            detail=f"Document A '{body.doc_id_a}' has no extracted clauses. Run clause extraction first via POST /api/clauses/{body.doc_id_a}.",
        )
    if not doc_b.clauses:
        raise HTTPException(
            status_code=400,
            detail=f"Document B '{body.doc_id_b}' has no extracted clauses. Run clause extraction first via POST /api/clauses/{body.doc_id_b}.",
        )

    try:
        comparison_result = await comparator.compare(body.doc_id_a, body.doc_id_b)
        return CompareResponse(
            comparison=comparison_result,
            results=comparison_result.pairs,
        )
    except ValueError as ve:
        raise HTTPException(status_code=404, detail=str(ve))
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Comparison failed: {str(e)}",
        )
