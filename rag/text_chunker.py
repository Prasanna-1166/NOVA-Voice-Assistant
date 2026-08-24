import re
from typing import List
from rag.document_models import Document, DocumentChunk


class TextChunker:
    """
    Deterministic text chunker preserving page metadata where applicable.
    """

    def __init__(self, chunk_size: int = 500, overlap: int = 50):
        self.chunk_size = chunk_size
        self.overlap = overlap

    def chunk_document(self, document: Document) -> List[DocumentChunk]:
        if not document.content or not document.content.strip():
            return []

        words = document.content.split()
        if not words:
            return []

        chunks: List[DocumentChunk] = []
        chunk_idx = 0
        start = 0

        while start < len(words):
            end = start + self.chunk_size
            chunk_words = words[start:end]
            chunk_text = " ".join(chunk_words)

            # Extract page number metadata if available in text block
            page_match = re.search(r"\[Page (\d+)\]", chunk_text)
            page_num = int(page_match.group(1)) if page_match else None

            chunks.append(
                DocumentChunk(
                    document_id=document.id,
                    chunk_index=chunk_idx,
                    text=chunk_text,
                    source_filename=document.filename,
                    page_number=page_num,
                    metadata={"source_path": document.source_path},
                )
            )

            chunk_idx += 1
            start += self.chunk_size - self.overlap
            if start >= len(words):
                break

        return chunks