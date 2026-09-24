"""
Document store service for managing ingested documents and extracted clauses.
Supports in-memory cache with fallback to /tmp on serverless environments (Vercel).
"""

from __future__ import annotations

import json
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

from pydantic import BaseModel, Field

from app.models.schemas import Clause


def _get_writable_dir(dir_name: str) -> Path:
    base_data = Path(__file__).resolve().parent.parent.parent / "data" / dir_name
    try:
        base_data.mkdir(parents=True, exist_ok=True)
        # Test write permission
        test_file = base_data / ".perm_check"
        test_file.touch()
        test_file.unlink()
        return base_data
    except Exception:
        tmp_data = Path(tempfile.gettempdir()) / "clausewise" / dir_name
        tmp_data.mkdir(parents=True, exist_ok=True)
        return tmp_data


STORAGE_DIR = _get_writable_dir("documents")
UPLOADS_DIR = _get_writable_dir("uploads")


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
    """In-memory cache with graceful storage persistence."""

    def __init__(self) -> None:
        self._memory: dict[str, DocumentRecord] = {}
        self._load_from_disk()
        self._seed_sample_documents()

    def _load_from_disk(self) -> None:
        try:
            for json_file in STORAGE_DIR.glob("*.json"):
                try:
                    data = json.loads(json_file.read_text(encoding="utf-8"))
                    doc = DocumentRecord.model_validate(data)
                    self._memory[doc.doc_id] = doc
                except Exception as e:
                    print(f"Warning: Failed to load document record {json_file}: {e}")
        except Exception:
            pass

    def _seed_sample_documents(self) -> None:
        if "doc-001" not in self._memory:
            try:
                fixtures_dir = Path(__file__).resolve().parent.parent.parent / "fixtures"
                rental_txt = fixtures_dir / "rental_agreement.txt"
                raw_text = (
                    rental_txt.read_text(encoding="utf-8")
                    if rental_txt.exists()
                    else "Residential Lease Agreement"
                )
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
            except Exception as e:
                print(f"[DocumentStore] Warning seeding sample doc: {e}")

    def save_file(self, doc_id: str, filename: str, content: bytes) -> str:
        safe_name = f"{doc_id}_{Path(filename).name}"
        target = UPLOADS_DIR / safe_name
        try:
            target.write_bytes(content)
            return str(target)
        except Exception as e:
            print(f"[DocumentStore] Warning saving upload bytes to disk: {e}")
            return str(target)

    def save(self, record: DocumentRecord) -> None:
        self._memory[record.doc_id] = record
        target = STORAGE_DIR / f"{record.doc_id}.json"
        try:
            target.write_text(
                record.model_dump_json(indent=2, by_alias=True), encoding="utf-8"
            )
        except Exception as e:
            print(f"[DocumentStore] Warning persisting record to disk: {e}")

    def get(self, doc_id: str) -> Optional[DocumentRecord]:
        return self._memory.get(doc_id)

    def update_clauses(
        self, doc_id: str, clauses: list[Clause]
    ) -> Optional[DocumentRecord]:
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