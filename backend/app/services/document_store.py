"""
Document store service for managing ingested documents and extracted clauses.
"""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

from pydantic import BaseModel, Field

from app.models.schemas import Clause

STORAGE_DIR = Path(__file__).resolve().parent.parent.parent / "data" / "documents"
UPLOADS_DIR = Path(__file__).resolve().parent.parent.parent / "data" / "uploads"


class DocumentRecord(BaseModel):
    doc_id: str = Field(alias="docId")
    file_name: str = Field(alias="fileName")
    file_path: Optional[str] = Field(alias="filePath", default=None)
    mime_type: str = Field(alias="mimeType", default="application/pdf")
    raw_text: str = Field(alias="rawText", default="")
    clauses: list[Clause] = Field(default_factory=list)
    created_at: str = Field(
        alias="createdAt",
        default_factory=lambda: datetime.now(timezone.utc).isoformat(),
    )

    model_config = {"populate_by_name": True}


class DocumentStore:
    """In-memory cache with JSON persistence."""

    def __init__(self) -> None:
        STORAGE_DIR.mkdir(parents=True, exist_ok=True)
        UPLOADS_DIR.mkdir(parents=True, exist_ok=True)
        self._memory: dict[str, DocumentRecord] = {}
        self._load_from_disk()
        self._seed_sample_documents()

    def _load_from_disk(self) -> None:
        for json_file in STORAGE_DIR.glob("*.json"):
            try:
                data = json.loads(json_file.read_text(encoding="utf-8"))
                doc = DocumentRecord.model_validate(data)
                self._memory[doc.doc_id] = doc
            except Exception as e:
                print(f"Warning: Failed to load document record {json_file}: {e}")

    def _seed_sample_documents(self) -> None:
        if "doc-001" not in self._memory:
            fixtures_dir = Path(__file__).resolve().parent.parent.parent / "fixtures"
            rental_txt = fixtures_dir / "rental_agreement.txt"
            raw_text = rental_txt.read_text(encoding="utf-8") if rental_txt.exists() else "Residential Lease Agreement"
            from app.services.gemini_client import gemini_client
            clauses = gemini_client._mock_extract_clauses(raw_text)
            self.save(
                DocumentRecord(
                    docId="doc-001",
                    fileName="sample_rental_agreement.pdf",
                    filePath=str(fixtures_dir / "rental_agreement.pdf"),
                    mimeType="application/pdf",
                    rawText=raw_text,
                    clauses=clauses,
                )
            )

    def save_file(self, doc_id: str, filename: str, content: bytes) -> str:
        safe_name = f"{doc_id}_{Path(filename).name}"
        target = UPLOADS_DIR / safe_name
        target.write_bytes(content)
        return str(target)

    def save(self, record: DocumentRecord) -> None:
        self._memory[record.doc_id] = record
        target = STORAGE_DIR / f"{record.doc_id}.json"
        target.write_text(record.model_dump_json(indent=2, by_alias=True), encoding="utf-8")

    def get(self, doc_id: str) -> Optional[DocumentRecord]:
        return self._memory.get(doc_id)

    def update_clauses(self, doc_id: str, clauses: list[Clause]) -> Optional[DocumentRecord]:
        doc = self.get(doc_id)
        if not doc:
            return None
        doc.clauses = clauses
        self.save(doc)
        return doc

    def list_all(self) -> list[DocumentRecord]:
        return list(self._memory.values())


# Singleton instance
document_store = DocumentStore()
