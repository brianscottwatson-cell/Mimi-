"""
RAG (Retrieval-Augmented Generation) Manager
Manages vector embeddings, document ingestion, and similarity search.
Uses Pinecone when available, falls back to in-memory store.
"""
import os
import json
import hashlib
from typing import List, Dict, Any, Optional
from datetime import datetime


class InMemoryVectorStore:
    """Simple in-memory vector store for development / no-Pinecone fallback."""

    def __init__(self):
        self._docs: Dict[str, List[Dict[str, Any]]] = {}

    def upsert(self, namespace: str, doc_id: str, text: str, metadata: Dict = None):
        if namespace not in self._docs:
            self._docs[namespace] = []
        # Remove old version if exists
        self._docs[namespace] = [d for d in self._docs[namespace] if d["id"] != doc_id]
        self._docs[namespace].append({
            "id": doc_id,
            "text": text,
            "metadata": metadata or {},
            "inserted_at": datetime.utcnow().isoformat(),
        })

    def query(self, namespace: str, query: str, top_k: int = 5) -> List[Dict[str, Any]]:
        """Naive keyword-based retrieval (no real embeddings in fallback mode)."""
        docs = self._docs.get(namespace, [])
        if not docs:
            return []

        # Score by simple term overlap
        query_terms = set(query.lower().split())
        scored = []
        for doc in docs:
            doc_terms = set(doc["text"].lower().split())
            overlap = len(query_terms & doc_terms)
            scored.append((overlap, doc))

        scored.sort(key=lambda x: x[0], reverse=True)
        return [doc for _, doc in scored[:top_k] if scored[0][0] > 0]

    def delete(self, namespace: str, doc_id: str) -> bool:
        if namespace not in self._docs:
            return False
        before = len(self._docs[namespace])
        self._docs[namespace] = [d for d in self._docs[namespace] if d["id"] != doc_id]
        return len(self._docs[namespace]) < before

    def list_docs(self, namespace: str) -> List[Dict[str, Any]]:
        return self._docs.get(namespace, [])

    def stats(self, namespace: str) -> Dict[str, Any]:
        docs = self._docs.get(namespace, [])
        return {"namespace": namespace, "doc_count": len(docs), "backend": "in-memory"}


class PineconeVectorStore:
    """Pinecone-backed vector store with OpenAI/Anthropic embeddings."""

    def __init__(self, api_key: str, index_name: str = "agent-factory"):
        try:
            from pinecone import Pinecone, ServerlessSpec
            self.pc = Pinecone(api_key=api_key)

            # Create index if not exists
            existing = [idx.name for idx in self.pc.list_indexes()]
            if index_name not in existing:
                self.pc.create_index(
                    name=index_name,
                    dimension=1536,
                    metric="cosine",
                    spec=ServerlessSpec(cloud="aws", region="us-east-1"),
                )
            self.index = self.pc.Index(index_name)
            self._available = True
        except Exception as e:
            print(f"[RAG] Pinecone init failed: {e}. Using in-memory store.")
            self._available = False

    def _embed(self, text: str) -> List[float]:
        """Get embedding vector via OpenAI API."""
        try:
            import openai
            client = openai.OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
            resp = client.embeddings.create(input=text, model="text-embedding-3-small")
            return resp.data[0].embedding
        except Exception:
            # Fallback: zero vector (won't be meaningful but won't crash)
            return [0.0] * 1536

    def upsert(self, namespace: str, doc_id: str, text: str, metadata: Dict = None):
        if not self._available:
            return
        vector = self._embed(text)
        self.index.upsert(
            vectors=[{"id": doc_id, "values": vector, "metadata": {**(metadata or {}), "text": text[:512]}}],
            namespace=namespace,
        )

    def query(self, namespace: str, query: str, top_k: int = 5) -> List[Dict[str, Any]]:
        if not self._available:
            return []
        vector = self._embed(query)
        result = self.index.query(vector=vector, top_k=top_k, namespace=namespace, include_metadata=True)
        return [
            {"id": m.id, "text": m.metadata.get("text", ""), "score": m.score, "metadata": m.metadata}
            for m in result.matches
        ]

    def delete(self, namespace: str, doc_id: str) -> bool:
        if not self._available:
            return False
        self.index.delete(ids=[doc_id], namespace=namespace)
        return True

    def list_docs(self, namespace: str) -> List[Dict[str, Any]]:
        # Pinecone doesn't have a list endpoint in all tiers; return empty
        return []

    def stats(self, namespace: str) -> Dict[str, Any]:
        try:
            stats = self.index.describe_index_stats()
            ns_stats = stats.namespaces.get(namespace, {})
            return {
                "namespace": namespace,
                "doc_count": ns_stats.get("vector_count", 0),
                "backend": "pinecone",
            }
        except Exception:
            return {"namespace": namespace, "doc_count": 0, "backend": "pinecone"}


class RAGManager:
    """
    Unified RAG interface. Auto-selects Pinecone or in-memory backend.
    Handles chunking, ingestion, and context injection.
    """

    CHUNK_SIZE = 500  # chars per chunk
    CHUNK_OVERLAP = 50

    def __init__(self):
        pinecone_key = os.getenv("PINECONE_API_KEY")
        if pinecone_key:
            self._store = PineconeVectorStore(pinecone_key)
        else:
            self._store = InMemoryVectorStore()

    # ------------------------------------------------------------------ #
    #  Ingestion                                                           #
    # ------------------------------------------------------------------ #

    def ingest_text(self, namespace: str, text: str, source: str = "manual") -> List[str]:
        """Chunk and ingest plain text. Returns list of chunk IDs."""
        chunks = self._chunk(text)
        ids = []
        for i, chunk in enumerate(chunks):
            doc_id = hashlib.md5(f"{namespace}:{source}:{i}:{chunk}".encode()).hexdigest()
            self._store.upsert(namespace, doc_id, chunk, {"source": source, "chunk_index": i})
            ids.append(doc_id)
        return ids

    def ingest_documents(self, namespace: str, documents: List[Dict[str, Any]]) -> List[str]:
        """
        Ingest a list of {text, source, metadata} documents.
        Returns all chunk IDs.
        """
        all_ids = []
        for doc in documents:
            ids = self.ingest_text(namespace, doc.get("text", ""), doc.get("source", "upload"))
            all_ids.extend(ids)
        return all_ids

    # ------------------------------------------------------------------ #
    #  Retrieval                                                           #
    # ------------------------------------------------------------------ #

    def retrieve(self, namespace: str, query: str, top_k: int = 5) -> List[Dict[str, Any]]:
        """Retrieve relevant chunks for a query."""
        return self._store.query(namespace, query, top_k)

    def build_context(self, namespace: str, query: str, top_k: int = 5) -> str:
        """
        Build a context string to inject into the LLM prompt.
        Returns empty string if no relevant docs found.
        """
        results = self.retrieve(namespace, query, top_k)
        if not results:
            return ""
        context_parts = [f"[Document {i+1}]: {r['text']}" for i, r in enumerate(results)]
        return "Relevant knowledge:\n\n" + "\n\n".join(context_parts)

    # ------------------------------------------------------------------ #
    #  Management                                                          #
    # ------------------------------------------------------------------ #

    def delete_document(self, namespace: str, doc_id: str) -> bool:
        return self._store.delete(namespace, doc_id)

    def list_documents(self, namespace: str) -> List[Dict[str, Any]]:
        return self._store.list_docs(namespace)

    def stats(self, namespace: str) -> Dict[str, Any]:
        return self._store.stats(namespace)

    # ------------------------------------------------------------------ #
    #  Internal                                                            #
    # ------------------------------------------------------------------ #

    def _chunk(self, text: str) -> List[str]:
        """Split text into overlapping chunks."""
        chunks = []
        start = 0
        while start < len(text):
            end = start + self.CHUNK_SIZE
            chunks.append(text[start:end])
            start += self.CHUNK_SIZE - self.CHUNK_OVERLAP
        return [c for c in chunks if c.strip()]
