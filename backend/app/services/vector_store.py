import math, os
from pathlib import Path
from typing import Any
from dotenv import load_dotenv
from app.knowledge.indian_statutes import STATUTE_CHUNKS

load_dotenv()
CHROMA_HOST = os.getenv('CHROMA_HOST', 'localhost')
CHROMA_PORT = int(os.getenv('CHROMA_PORT', '8000'))
PERSIST_DIR = Path(__file__).resolve().parent.parent.parent / 'data' / 'chroma_db'

try:
    import chromadb
    HAS_CHROMADB = True
except ImportError:
    HAS_CHROMADB = False

def cosine_similarity(v1: list[float], v2: list[float]) -> float:
    if not v1 or not v2 or len(v1) != len(v2): return 0.0
    dot = sum(a * b for a, b in zip(v1, v2))
    norm1 = math.sqrt(sum(a * a for a in v1))
    norm2 = math.sqrt(sum(b * b for b in v2))
    if norm1 == 0 or norm2 == 0: return 0.0
    return dot / (norm1 * norm2)

class VectorStore:
    def __init__(self) -> None:
        self.use_chroma = HAS_CHROMADB
        self._embedded_chunks: list[dict[str, Any]] = []
        if self.use_chroma:
            try:
                PERSIST_DIR.mkdir(parents=True, exist_ok=True)
                self.client = self._init_chroma_client()
                self.collection = self.client.get_or_create_collection(
                    name='indian_statutes',
                    metadata={'hnsw:space': 'cosine'},
                )
                self._seed_statutes_if_needed()
            except Exception as e:
                print(f'[VectorStore] ChromaDB init failed ({e}). Using lightweight store.')
                self.use_chroma = False

    def _init_chroma_client(self) -> Any:
        if os.getenv('USE_REMOTE_CHROMA', 'false').lower() == 'true':
            try:
                client = chromadb.HttpClient(host=CHROMA_HOST, port=CHROMA_PORT)
                client.heartbeat()
                return client
            except Exception: pass
        try: return chromadb.PersistentClient(path=str(PERSIST_DIR))
        except Exception: return chromadb.EphemeralClient()

    def _seed_statutes_if_needed(self) -> None:
        if not self.use_chroma: return
        if self.collection.count() >= len(STATUTE_CHUNKS): return
        from app.services.gemini_client import gemini_client
        ids, documents, metadatas, embeddings = [], [], [], []
        for chunk in STATUTE_CHUNKS:
            chunk_id = chunk['id']
            doc_text = f"{chunk['citation']} - {chunk['title']}\n{chunk['text']}"
            meta = {
                'act': chunk['act'], 'section': chunk['section'],
                'citation': chunk['citation'], 'title': chunk['title'], 'category': chunk['category'],
            }
            vec = gemini_client.embed_text_sync(doc_text)
            ids.append(chunk_id); documents.append(doc_text); metadatas.append(meta); embeddings.append(vec)
        self.collection.upsert(ids=ids, documents=documents, metadatas=metadatas, embeddings=embeddings)

    async def _ensure_memory_seeded(self) -> None:
        if self._embedded_chunks: return
        from app.services.gemini_client import gemini_client
        for chunk in STATUTE_CHUNKS:
            doc_text = f"{chunk['citation']} - {chunk['title']}\n{chunk['text']}"
            vec = await gemini_client.embed_text(doc_text)
            self._embedded_chunks.append({'chunk': chunk, 'doc_text': doc_text, 'embedding': vec})

    async def retrieve_relevant_law(self, clause_text: str, top_k: int = 3) -> list[dict[str, Any]]:
        if not clause_text.strip(): return []
        from app.services.gemini_client import gemini_client
        query_embedding = await gemini_client.embed_text(clause_text)

        if self.use_chroma:
            try:
                results = self.collection.query(
                    query_embeddings=[query_embedding],
                    n_results=min(top_k, self.collection.count() or top_k),
                    include=['documents', 'metadatas', 'distances'],
                )
                matches: list[dict[str, Any]] = []
                if results and results.get('ids') and results['ids'][0]:
                    ids = results['ids'][0]
                    docs = results['documents'][0] if results.get('documents') else [''] * len(ids)
                    metas = results['metadatas'][0] if results.get('metadatas') else [{}] * len(ids)
                    dists = results['distances'][0] if results.get('distances') else [0.0] * len(ids)
                    for i in range(len(ids)):
                        meta = metas[i] or {}
                        matches.append({
                            'id': ids[i], 'citation': meta.get('citation', ''),
                            'section': meta.get('section', ''), 'act': meta.get('act', ''),
                            'title': meta.get('title', ''), 'category': meta.get('category', ''),
                            'text': docs[i], 'distance': dists[i],
                            'similarity': round(1.0 - dists[i], 4) if dists[i] is not None else 0.0,
                        })
                    return matches
            except Exception as e:
                print(f'[VectorStore] ChromaDB query failed ({e}). Falling back to memory.')

        await self._ensure_memory_seeded()
        scored = []
        for item in self._embedded_chunks:
            sim = cosine_similarity(query_embedding, item['embedding'])
            chunk = item['chunk']
            scored.append({
                'id': chunk['id'], 'citation': chunk['citation'], 'section': chunk['section'],
                'act': chunk['act'], 'title': chunk['title'], 'category': chunk['category'],
                'text': item['doc_text'], 'distance': round(1.0 - sim, 4), 'similarity': round(sim, 4),
            })
        scored.sort(key=lambda x: x['similarity'], reverse=True)
        return scored[:top_k]

vector_store = VectorStore()

async def retrieve_relevant_law(clause_text: str, top_k: int = 3) -> list[dict[str, Any]]:
    return await vector_store.retrieve_relevant_law(clause_text=clause_text, top_k=top_k)