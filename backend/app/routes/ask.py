"""
Ask route - grounded document Q&A with clause citations and statute references.
"""

from fastapi import APIRouter, HTTPException

from app.models.schemas import AskRequest, AskResponse
from app.services.document_qa import document_qa
from app.services.document_store import document_store

router = APIRouter(prefix="/ask", tags=["ask"])

MAX_HISTORY_TURNS = 5


@router.post("/", response_model=AskResponse)
async def ask_question(body: AskRequest) -> AskResponse:
    """
    Ask a free-form legal question about an ingested document.
    - Scoped strictly to the document's clauses + retrieved Indian statutes.
    - Mentions specific clause IDs backing the answer.
    - Rejects questions outside document scope with 'this document doesn't address that'.
    - Maintains conversational history context across recent turns.
    - Concludes with varied, natural informational disclaimers.
    """
    # Validate: question must not be empty
    question = body.question.strip()
    if not question:
        raise HTTPException(
            status_code=400,
            detail="Question cannot be empty. Please ask a specific question about the document.",
        )

    # Validate: document must exist
    doc = document_store.get(body.doc_id)
    if not doc:
        raise HTTPException(
            status_code=404,
            detail=f"Document '{body.doc_id}' not found. Please upload it via /api/ingest/ first.",
        )

    # Server-side history truncation: keep only last N turns
    history = body.history[-MAX_HISTORY_TURNS:] if body.history else []

    try:
        return await document_qa.ask(
            doc_id=body.doc_id,
            question=question,
            history=history,
        )
    except ValueError as ve:
        raise HTTPException(status_code=404, detail=str(ve))
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Q&A query failed: {str(e)}",
        )
