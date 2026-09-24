"""
Ingest route - handles multimodal PDF/image upload and raw text extraction via Gemini.
"""

import uuid
from fastapi import APIRouter, File, HTTPException, UploadFile

from app.models.schemas import DocumentSummary, IngestResponse
from app.services.document_store import DocumentRecord, document_store
from app.services.gemini_client import gemini_client

router = APIRouter(prefix="/ingest", tags=["ingest"])

ALLOWED_MIME_TYPES = {
    "application/pdf",
    "image/png",
    "image/jpeg",
    "image/jpg",
    "image/webp",
    "text/plain",
}


MAX_FILE_SIZE = 25 * 1024 * 1024  # 25 MB


@router.post("/", response_model=IngestResponse)
async def ingest_document(file: UploadFile = File(...)) -> IngestResponse:
    """
    Upload a PDF or image legal document.
    Sends raw file bytes directly to Gemini for multimodal document understanding,
    stores the raw text + file reference, and returns a docId.
    """
    filename = file.filename or "uploaded_document.pdf"
    content_type = file.content_type or "application/pdf"

    # Validate file format
    if content_type not in ALLOWED_MIME_TYPES and not filename.lower().endswith(
        (".pdf", ".png", ".jpg", ".jpeg", ".webp", ".txt")
    ):
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported file format '{content_type}'. Please upload a PDF or image file.",
        )

    file_bytes = await file.read()
    if not file_bytes or len(file_bytes) == 0:
        raise HTTPException(status_code=400, detail="Uploaded file is empty or corrupted.")

    if len(file_bytes) > MAX_FILE_SIZE:
        raise HTTPException(
            status_code=413,
            detail=f"File size exceeds 25MB limit (file is {len(file_bytes) / (1024*1024):.1f}MB).",
        )

    # Check for corrupt PDF headers if file claims to be PDF
    if (content_type == "application/pdf" or filename.lower().endswith(".pdf")) and not file_bytes.startswith(b"%PDF"):
        # If it doesn't have PDF magic number, verify if it's text or truly corrupted
        if b"%PDF" not in file_bytes[:1024]:
            raise HTTPException(
                status_code=400,
                detail="The uploaded PDF file appears to be corrupted or invalid.",
            )

    doc_id = f"doc-{uuid.uuid4().hex[:8]}"

    # Save uploaded file to disk
    file_path = document_store.save_file(doc_id, filename, file_bytes)

    # Multimodal text extraction directly with Gemini (no separate OCR library)
    extracted_text = await gemini_client.extract_text_from_document(
        file_bytes=file_bytes,
        mime_type=content_type,
        filename=filename,
    )

    # Persist document record
    doc_record = DocumentRecord(
        docId=doc_id,
        fileName=filename,
        filePath=file_path,
        mimeType=content_type,
        rawText=extracted_text,
        clauses=[],
    )
    document_store.save(doc_record)

    # Provide DocumentSummary for immediate UI rendering
    plain_summary = (
        extracted_text[:300].strip() + "..."
        if len(extracted_text) > 300
        else extracted_text
    )

    summary = DocumentSummary(
        docId=doc_id,
        fileName=filename,
        plainSummary=plain_summary,
        clauses=[],
    )

    return IngestResponse(
        docId=doc_id,
        fileName=filename,
        rawText=extracted_text,
        filePath=file_path,
        mimeType=content_type,
        document=summary,
    )
