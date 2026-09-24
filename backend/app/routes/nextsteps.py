"""
Next Steps route - actionable checklists and lawyer consultation questions for flagged clauses.
"""

from fastapi import APIRouter, HTTPException

from app.models.schemas import NextStepsRequest, NextStepsResponse
from app.services.document_store import document_store
from app.services.next_steps_generator import next_steps_generator

router = APIRouter(prefix="/nextsteps", tags=["nextsteps"])


@router.post("/{doc_id}", response_model=NextStepsResponse)
async def generate_next_steps_for_doc(doc_id: str) -> NextStepsResponse:
    """
    Generate structured next steps for an ingested document:
    - Generates 2-4 concrete, non-legal-advice personal action items for every MEDIUM/HIGH risk clause.
    - Generates 1-3 specific questions for legal counsel to read aloud.
    - Generates a 3-5 bullet executive document brief ready for consultation export.
    """
    # Validate: document must exist
    doc = document_store.get(doc_id)
    if not doc:
        raise HTTPException(
            status_code=404,
            detail=f"Document '{doc_id}' not found. Please upload it via /api/ingest/ first.",
        )

    # Validate: clauses must have been extracted
    if not doc.clauses:
        raise HTTPException(
            status_code=400,
            detail=f"Document '{doc_id}' has no extracted clauses. Run clause extraction first via POST /api/clauses/{doc_id}.",
        )

    try:
        return await next_steps_generator.generate_next_steps(doc_id)
    except ValueError as ve:
        raise HTTPException(status_code=404, detail=str(ve))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Next steps generation failed: {str(e)}")


@router.post("/", response_model=NextStepsResponse)
async def generate_next_steps_body(body: NextStepsRequest) -> NextStepsResponse:
    """Body-based endpoint for next steps generation."""
    return await generate_next_steps_for_doc(body.doc_id)
