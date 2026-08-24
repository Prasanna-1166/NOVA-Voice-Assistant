from typing import Optional, List, Dict, Any
from core.llm import OllamaProvider
from rag.document_loader import DocumentLoader
from rag.text_chunker import TextChunker
from rag.embedding_service import EmbeddingService
from rag.vector_store import LocalVectorStore
from rag.retriever import Retriever


class RAGPipeline:
    """
    Main orchestration layer for document ingestion and grounded question answering.
    """

    def __init__(
        self,
        llm_provider: Optional[OllamaProvider] = None,
        vector_store: Optional[LocalVectorStore] = None,
        embedding_service: Optional[EmbeddingService] = None,
    ):
        self.llm_provider = llm_provider or OllamaProvider()
        self.vector_store = vector_store or LocalVectorStore()
        self.embedding_service = embedding_service or EmbeddingService()
        self.retriever = Retriever(self.vector_store, self.embedding_service)
        self.chunker = TextChunker()

    def ingest_document(self, file_path: str) -> str:
        doc = DocumentLoader.load_document(file_path)
        chunks = self.chunker.chunk_document(doc)
        if not chunks:
            return f"No readable chunks extracted from '{doc.filename}'."

        embeddings = self.embedding_service.generate_batch_embeddings([c.text for c in chunks])
        self.vector_store.add_chunks(chunks, embeddings)
        return f"Successfully ingested '{doc.filename}' ({len(chunks)} chunks indexed), Boss."

    def query(self, question: str) -> str:
        # Retrieve top 2 most relevant chunks to keep inference lightweight and fast
        retrieved_chunks = self.retriever.retrieve(question, top_k=2)

        if not retrieved_chunks:
            return "I couldn't find enough relevant information about that in your indexed documents, Boss."

        # Build grounded context block
        context_blocks = []
        sources = set()

        for item in retrieved_chunks:
            c = item.chunk
            page_str = f" — Page {c.page_number}" if c.page_number else ""
            source_tag = f"{c.source_filename}{page_str}"
            sources.add(source_tag)
            context_blocks.append(f"[Source: {source_tag}]\n{c.text}")

        context_text = "\n\n".join(context_blocks)

        prompt = (
            f"You are NOVA. Answer the user's question STRICTLY based on the provided document excerpts below.\n"
            f"If the answer is not present in the context, explicitly state that the information was not found in the documents.\n\n"
            f"--- DOCUMENT CONTEXT ---\n{context_text}\n\n"
            f"--- USER QUESTION ---\n{question}"
        )

        # Pass 120-second timeout explicitly to prevent HTTP timeout errors
        llm_response = self.llm_provider.generate(prompt=prompt, timeout=120)

        # Handle LLM failure or timeout response gracefully
        if not llm_response or llm_response.startswith("[!]"):
            return f"Error executing grounded query, Boss: {llm_response}"

        sources_list = "\n".join([f"- {s}" for s in sorted(list(sources))])
        return f"{llm_response}\n\n**Sources:**\n{sources_list}"

    def list_documents(self) -> List[str]:
        return self.vector_store.list_documents()

    def remove_document(self, filename: str) -> str:
        if self.vector_store.delete_document(filename):
            return f"Removed document '{filename}' from local knowledge base, Boss."
        return f"Document '{filename}' was not found in local knowledge base, Boss."


default_rag_pipeline = RAGPipeline()