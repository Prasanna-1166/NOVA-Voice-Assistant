import json
import os
import time
from typing import Any, Dict, List, Optional


class RAGEvaluator:
    """
    Offline RAG retrieval evaluation.

    Evaluates:
    - Recall@1
    - Recall@3
    - Recall@5
    - MRR
    - Average retrieval latency

    The evaluator uses the existing RAG pipeline and does not
    modify the vector store or indexed documents.
    """

    def __init__(
        self,
        dataset_path: str = "evaluation/rag_dataset.json",
        rag_pipeline: Optional[Any] = None,
    ):
        self.dataset_path = dataset_path

        # Automatically use the project's default RAG pipeline
        # when one is not explicitly supplied.
        if rag_pipeline is None:
            try:
                from rag.rag_pipeline import default_rag_pipeline

                self.rag_pipeline = default_rag_pipeline

            except Exception as exc:
                print(
                    f"[WARNING] Could not load default RAG pipeline: {exc}"
                )
                self.rag_pipeline = None

        else:
            self.rag_pipeline = rag_pipeline

        self.data: List[Dict[str, Any]] = []

        self.load_dataset()

    # ==========================================================
    # Dataset
    # ==========================================================

    def load_dataset(self) -> None:
        """Load evaluation samples from the JSON dataset."""

        if not os.path.exists(self.dataset_path):
            print(
                f"[WARNING] Evaluation dataset not found: "
                f"{self.dataset_path}"
            )
            self.data = []
            return

        try:
            with open(
                self.dataset_path,
                "r",
                encoding="utf-8",
            ) as file:
                payload = json.load(file)

            self.data = payload.get("samples", [])

        except (json.JSONDecodeError, OSError) as exc:
            print(
                f"[WARNING] Failed to load evaluation dataset: {exc}"
            )
            self.data = []

    # ==========================================================
    # Text extraction
    # ==========================================================

    @staticmethod
    def _chunk_to_text(chunk: Any) -> str:
        """
        Convert a retrieved chunk into searchable text.

        Supports:
        - dictionaries
        - objects with content/text attributes
        - plain strings
        """

        if isinstance(chunk, dict):
            return str(
                chunk.get(
                    "content",
                    chunk.get(
                        "text",
                        chunk.get("page_content", ""),
                    ),
                )
            )

        if hasattr(chunk, "content"):
            return str(chunk.content)

        if hasattr(chunk, "text"):
            return str(chunk.text)

        if hasattr(chunk, "page_content"):
            return str(chunk.page_content)

        return str(chunk)

    @staticmethod
    def _normalize_text(text: str) -> str:
        """Normalize text for simple lexical matching."""

        return " ".join(
            text.lower().strip().split()
        )

    @classmethod
    def _is_relevant(
        cls,
        chunk: Any,
        expected_text: str,
    ) -> bool:
        """
        Determine whether a retrieved chunk is relevant.

        Uses token overlap rather than requiring the entire
        expected context to appear verbatim.
        """

        if not expected_text:
            return False

        chunk_text = cls._normalize_text(
            cls._chunk_to_text(chunk)
        )

        expected_tokens = [
            token
            for token in cls._normalize_text(
                expected_text
            ).split()
            if len(token) >= 4
        ]

        if not chunk_text or not expected_tokens:
            return False

        # Count how many meaningful expected tokens occur
        # in the retrieved chunk.
        matches = sum(
            1
            for token in expected_tokens
            if token in chunk_text
        )

        # A small overlap threshold makes the benchmark
        # more tolerant of chunking differences.
        required_matches = max(
            2,
            min(5, len(expected_tokens) // 3),
        )

        return matches >= required_matches

    # ==========================================================
    # Retrieval
    # ==========================================================

    def _retrieve(
        self,
        question: str,
        top_k: int,
    ) -> List[Any]:
        """Run the project's existing RAG retriever."""

        if self.rag_pipeline is None:
            return []

        if not hasattr(self.rag_pipeline, "retriever"):
            return []

        try:
            return self.rag_pipeline.retriever.retrieve(
                question=question,
                top_k=top_k,
            )

        except TypeError:
            # Compatibility with retrievers using a
            # positional question argument.
            try:
                return self.rag_pipeline.retriever.retrieve(
                    question,
                    top_k=top_k,
                )

            except Exception:
                return []

        except Exception:
            return []

    # ==========================================================
    # Evaluation
    # ==========================================================

    def evaluate_retrieval(
        self,
        top_k: int = 5,
    ) -> Dict[str, float]:
        """
        Evaluate retrieval performance.

        Returns:
            recall_at_1
            recall_at_3
            recall_at_5
            mrr
            avg_latency_ms
        """

        if not self.data:
            print(
                "[ERROR] Evaluation dataset is empty."
            )

            return {
                "recall_at_1": 0.0,
                "recall_at_3": 0.0,
                "recall_at_5": 0.0,
                "mrr": 0.0,
                "avg_latency_ms": 0.0,
            }

        if self.rag_pipeline is None:
            print(
                "[ERROR] RAG pipeline is not available."
            )

            return {
                "recall_at_1": 0.0,
                "recall_at_3": 0.0,
                "recall_at_5": 0.0,
                "mrr": 0.0,
                "avg_latency_ms": 0.0,
            }

        total_queries = len(self.data)

        hits_at_1 = 0
        hits_at_3 = 0
        hits_at_5 = 0

        reciprocal_ranks: List[float] = []
        latencies: List[float] = []

        print()
        print("=" * 60)
        print("NOVA V2 - RAG RETRIEVAL EVALUATION")
        print("=" * 60)
        print(f"Evaluation samples : {total_queries}")
        print(f"Maximum Top-K      : {top_k}")
        print()

        for index, sample in enumerate(
            self.data,
            start=1,
        ):
            question = sample.get(
                "question",
                "",
            )

            expected_context = sample.get(
                "document_context",
                "",
            )

            print(
                f"[{index}/{total_queries}] "
                f"{question}"
            )

            start_time = time.perf_counter()

            retrieved_chunks = self._retrieve(
                question=question,
                top_k=top_k,
            )

            elapsed_ms = (
                time.perf_counter() - start_time
            ) * 1000

            latencies.append(elapsed_ms)

            found_rank: Optional[int] = None

            for rank, chunk in enumerate(
                retrieved_chunks,
                start=1,
            ):
                if self._is_relevant(
                    chunk,
                    expected_context,
                ):
                    found_rank = rank
                    break

            if found_rank == 1:
                hits_at_1 += 1

            if (
                found_rank is not None
                and found_rank <= 3
            ):
                hits_at_3 += 1

            if (
                found_rank is not None
                and found_rank <= 5
            ):
                hits_at_5 += 1

            if found_rank is not None:
                reciprocal_ranks.append(
                    1.0 / found_rank
                )

                print(
                    f"    Relevant chunk rank : "
                    f"{found_rank}"
                )

            else:
                reciprocal_ranks.append(0.0)

                print(
                    "    Relevant chunk rank : "
                    "Not found"
                )

            print(
                f"    Retrieval latency   : "
                f"{elapsed_ms:.2f} ms"
            )

            print()

        recall_at_1 = (
            hits_at_1 / total_queries
        )

        recall_at_3 = (
            hits_at_3 / total_queries
        )

        recall_at_5 = (
            hits_at_5 / total_queries
        )

        mrr = (
            sum(reciprocal_ranks)
            / total_queries
        )

        avg_latency = (
            sum(latencies)
            / len(latencies)
            if latencies
            else 0.0
        )

        metrics = {
            "recall_at_1": recall_at_1,
            "recall_at_3": recall_at_3,
            "recall_at_5": recall_at_5,
            "mrr": mrr,
            "avg_latency_ms": avg_latency,
        }

        # ======================================================
        # Final Results
        # ======================================================

        print("=" * 60)
        print("RAG EVALUATION RESULTS")
        print("=" * 60)

        print(
            f"Recall@1            : "
            f"{recall_at_1:.4f} "
            f"({recall_at_1 * 100:.2f}%)"
        )

        print(
            f"Recall@3            : "
            f"{recall_at_3:.4f} "
            f"({recall_at_3 * 100:.2f}%)"
        )

        print(
            f"Recall@5            : "
            f"{recall_at_5:.4f} "
            f"({recall_at_5 * 100:.2f}%)"
        )

        print(
            f"MRR                 : "
            f"{mrr:.4f}"
        )

        print(
            f"Average Latency     : "
            f"{avg_latency:.2f} ms"
        )

        print("=" * 60)

        return metrics


# ==============================================================
# Standalone execution
# ==============================================================

if __name__ == "__main__":

    evaluator = RAGEvaluator()

    print(
        f"Loaded {len(evaluator.data)} "
        f"evaluation samples."
    )

    if evaluator.data and evaluator.rag_pipeline:
        evaluator.evaluate_retrieval(
            top_k=5
        )

    elif not evaluator.data:
        print(
            "[ERROR] No evaluation samples available."
        )

    else:
        print(
            "[ERROR] RAG pipeline could not be loaded."
        )