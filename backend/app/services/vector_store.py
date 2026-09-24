"""
ChromaDB vector store service for Indian legal statute grounding (RAG).

Manages statutory embeddings and semantic law retrieval.
"""

from __future__ import annotations

import os
from pathlib import Path
from typing import Any, Optional

import chromadb
from dotenv import load_dotenv

from app.knowledge.indian_statutes import STATUTE_CHUNKS, StatuteChunk

load_dotenv()

CHROMA_HOST = os.getenv("CHROMA_HOST", "localhost")
CHROMA_PORT = int(os.getenv("CHROMA_PORT", "8000"))
PERSIST_DIR = Path(__file__).resolve().parent.parent.parent / "data" / "chroma_db"


class VectorStore:
    """Interface to ChromaDB with fallback to persistent local storage."""

    def __init__(self) -> None:
        PERSIST_DIR.mkdir(parents=True, exist_ok=True)
        self.client = self._init_chroma_client()
        self.collection = self.client.get_or_create_collection(
            name="indian_statutes",
            metadata={"hnsw:space": "cosine"},
        )
        self._seed_statutes_if_needed()

    def _init_chroma_client(self) -> chromadb.ClientAPI:
        """Connect to HTTP ChromaDB server if available; otherwise use local persistent client."""
        # Check if remote ChromaDB is reachable
        if os.getenv("USE_REMOTE_CHROMA", "false").lower() == "true":
            try:
                client = chromadb.HttpClient(host=CHROMA_HOST, port=CHROMA_PORT)
                client.heartbeat()
                print(f"[VectorStore] Connected to remote ChromaDB at {CHROMA_HOST}:{CHROMA_PORT}")
                return client
            except Exception as e:
                print(f"[VectorStore] Could not connect to remote ChromaDB ({e}). Using local persistent client.")

        print(f"[VectorStore] Initializing persistent local ChromaDB at {PERSIST_DIR}")
        try:
            return chromadb.PersistentClient(path=str(PERSIST_DIR))
        except Exception as e:
            print(f"[VectorStore] Local persistent client failed ({e}). Falling back to EphemeralClient.")
            return chromadb.EphemeralClient()

    def _seed_statutes_if_needed(self) -> None:
        """Index all statutory excerpts into ChromaDB if not already indexed."""
        current_count = self.collection.count()
        if current_count >= len(STATUTE_CHUNKS):
            return

        print(f"[VectorStore] Seeding {len(STATUTE_CHUNKS)} Indian statutory chunks into ChromaDB...")
        from app.services.gemini_client import gemini_client

        ids: list[str] = []
        documents: list[str] = []
        metadatas: list[dict[str, Any]] = []
        embeddings: list[list[float]] = []

        for chunk in STATUTE_CHUNKS:
            chunk_id = chunk["id"]
            doc_text = f"{chunk['citation']} - {chunk['title']}\n{chunk['text']}"
            meta = {
                "act": chunk["act"],
                "section": chunk["section"],
                "citation": chunk["citation"],
                "title": chunk["title"],
                "category": chunk["category"],
            }
            # Generate embedding synchronously for seeding
            vec = gemini_client.embed_text_sync(doc_text)

            ids.append(chunk_id)
            documents.append(doc_text)
            metadatas.append(meta)
            embeddings.append(vec)

        self.collection.upsert(
            ids=ids,
            documents=documents,
            metadatas=metadatas,
            embeddings=embeddings,
        )
        print(f"[VectorStore] Successfully indexed {self.collection.count()} statute sections.")

    async def retrieve_relevant_law(
        self, clause_text: str, top_k: int = 3
    ) -> list[dict[str, Any]]:
        """
        Embed a clause and query ChromaDB for the top matching statute chunks.
        """
        if not clause_text.strip():
            return []

        from app.services.gemini_client import gemini_client

        query_embedding = await gemini_client.embed_text(clause_text)

        results = self.collection.query(
            query_embeddings=[query_embedding],
            n_results=min(top_k, self.collection.count() or top_k),
            include=["documents", "metadatas", "distances"],
        )

        matches: list[dict[str, Any]] = []
        if not results or not results["ids"] or not results["ids"][0]:
            return matches

        ids = results["ids"][0]
        docs = results["documents"][0] if results["documents"] else [""] * len(ids)
        metas = results["metadatas"][0] if results["metadatas"] else [{}] * len(ids)
        dists = results["distances"][0] if results["distances"] else [0.0] * len(ids)

        for i in range(len(ids)):
            meta = metas[i] or {}
            matches.append(
                {
                    "id": ids[i],
                    "citation": meta.get("citation", ""),
                    "section": meta.get("section", ""),
                    "act": meta.get("act", ""),
                    "title": meta.get("title", ""),
                    "category": meta.get("category", ""),
                    "text": docs[i],
                    "distance": dists[i],
                    # Cosine distance to similarity (1 - dist)
                    "similarity": round(1.0 - dists[i], 4) if dists[i] is not None else 0.0,
                }
            )

        return matches


# Singleton instance
vector_store = VectorStore()


# Service function as requested in specification
async def retrieve_relevant_law(clause_text: str, top_k: int = 3) -> list[dict[str, Any]]:
    """
    Retrieve top_k matching Indian statute chunks with citations for a given clause text.
    """
    return await vector_store.retrieve_relevant_law(clause_text=clause_text, top_k=top_k)
