import json
from pathlib import Path
from typing import List, Dict, Any, Optional
import numpy as np
from rag.document_models import DocumentChunk, RetrievedChunk


class LocalVectorStore:
    """
    Lightweight, offline vector store utilizing NumPy and JSON disk persistence.
    Stored in Documents/NOVA/rag/vector_store.json.
    """

    def __init__(self, storage_path: Optional[Path] = None):
        if storage_path is None:
            base_dir = Path.home() / "Documents" / "NOVA" / "rag"
            base_dir.mkdir(parents=True, exist_ok=True)
            self.file_path = base_dir / "vector_store.json"
        else:
            self.file_path = storage_path
            self.file_path.parent.mkdir(parents=True, exist_ok=True)

        self.records: List[Dict[str, Any]] = []
        self._load()

    def _load(self) -> None:
        if self.file_path.exists():
            try:
                with open(self.file_path, "r", encoding="utf-8") as f:
                    self.records = json.load(f)
            except Exception:
                self.records = []
        else:
            self._save()

    def _save(self) -> None:
        with open(self.file_path, "w", encoding="utf-8") as f:
            json.dump(self.records, f, indent=2)

    def add_chunks(self, chunks: List[DocumentChunk], embeddings: List[List[float]]) -> None:
        for chunk, emb in zip(chunks, embeddings):
            if not emb:
                continue
            rec = {
                "id": chunk.id,
                "document_id": chunk.document_id,
                "chunk_index": chunk.chunk_index,
                "text": chunk.text,
                "source_filename": chunk.source_filename,
                "page_number": chunk.page_number,
                "metadata": chunk.metadata,
                "embedding": emb,
            }
            self.records.append(rec)
        self._save()

    def search(self, query_embedding: List[float], top_k: int = 5, threshold: float = 0.2) -> List[RetrievedChunk]:
        if not self.records or not query_embedding:
            return []

        q_vec = np.array(query_embedding, dtype=np.float32)
        q_norm = np.linalg.norm(q_vec)
        if q_norm == 0:
            return []

        results = []
        for rec in self.records:
            doc_vec = np.array(rec["embedding"], dtype=np.float32)
            doc_norm = np.linalg.norm(doc_vec)
            if doc_norm == 0:
                continue

            similarity = float(np.dot(q_vec, doc_vec) / (q_norm * doc_norm))
            if similarity >= threshold:
                chunk = DocumentChunk(
                    id=rec["id"],
                    document_id=rec["document_id"],
                    chunk_index=rec["chunk_index"],
                    text=rec["text"],
                    source_filename=rec["source_filename"],
                    page_number=rec.get("page_number"),
                    metadata=rec.get("metadata", {}),
                )
                results.append(RetrievedChunk(chunk=chunk, similarity_score=similarity))

        results.sort(key=lambda x: x.similarity_score, reverse=True)
        return results[:top_k]

    def delete_document(self, filename_or_id: str) -> bool:
        clean = filename_or_id.lower().strip()
        initial_len = len(self.records)
        self.records = [
            r for r in self.records
            if r["source_filename"].lower() != clean and r["document_id"].lower() != clean
        ]
        if len(self.records) < initial_len:
            self._save()
            return True
        return False

    def list_documents(self) -> List[str]:
        filenames = set(r["source_filename"] for r in self.records)
        return sorted(list(filenames))

    def clear(self) -> None:
        self.records = []
        self._save()