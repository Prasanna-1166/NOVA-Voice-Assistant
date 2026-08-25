import time
import json
import os

class RAGEvaluator:
    def __init__(self, dataset_path="evaluation/rag_dataset.json", rag_pipeline=None):
        self.dataset_path = dataset_path
        self.rag_pipeline = rag_pipeline
        self.load_dataset()

    def load_dataset(self):
        if os.path.exists(self.dataset_path):
            with open(self.dataset_path, "r") as f:
                self.data = json.load(f).get("samples", [])
        else:
            self.data = []

    def evaluate_retrieval(self, top_k=5):
        if not self.data or not self.rag_pipeline:
            print("Evaluation dataset empty or RAG pipeline not provided.")
            return {"recall_at_5": 0.0, "mrr": 0.0, "avg_latency_ms": 0.0}

        total_queries = len(self.data)
        hits_at_5 = 0
        reciprocal_ranks = []
        latencies = []

        for sample in self.data:
            query = sample["question"]
            expected_text = sample.get("document_context", "")

            start_time = time.time()
            try:
                retrieved_chunks = self.rag_pipeline.retriever.retrieve(question=query, top_k=top_k)
            except Exception:
                retrieved_chunks = []
            elapsed = (time.time() - start_time) * 1000
            latencies.append(elapsed)

            # Check if relevant text matches retrieved chunks
            found_rank = None
            for idx, chunk in enumerate(retrieved_chunks):
                chunk_content = getattr(chunk, "content", str(chunk))
                if any(word in chunk_content.lower() for word in expected_text.lower().split()[:5]):
                    found_rank = idx + 1
                    break

            if found_rank and found_rank <= 5:
                hits_at_5 += 1

            if found_rank:
                reciprocal_ranks.append(1.0 / found_rank)
            else:
                reciprocal_ranks.append(0.0)

        recall_5 = hits_at_5 / total_queries if total_queries > 0 else 0.0
        mrr = sum(reciprocal_ranks) / total_queries if total_queries > 0 else 0.0
        avg_latency = sum(latencies) / len(latencies) if latencies else 0.0

        metrics = {
            "recall_at_5": recall_5,
            "mrr": mrr,
            "avg_latency_ms": avg_latency
        }
        return metrics

if __name__ == "__main__":
    evaluator = RAGEvaluator()
    print(f"Loaded {len(evaluator.data)} evaluation samples.")