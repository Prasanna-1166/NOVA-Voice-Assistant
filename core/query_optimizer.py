class QueryOptimizer:
    """
    Analyzes and optimizes user queries before RAG retrieval.
    Preserves original query while providing search-optimized variations.
    """
    
    def __init__(self):
        pass

    def analyze_and_optimize(self, query: str) -> dict:
        if not query or not query.strip():
            return {
                "original_query": "",
                "optimized_query": "",
                "query_type": "GENERAL",
                "safe_to_process": False
            }

        cleaned_query = query.strip()
        lower_q = cleaned_query.lower()

        # Simple intent classification rules
        query_type = "FACTUAL"
        if any(w in lower_q for w in ["what is", "define", "definition"]):
            query_type = "DEFINITION"
        elif any(w in lower_q for w in ["summarize", "summary", "overview"]):
            query_type = "SUMMARY"
        elif any(w in lower_q for w in ["compare", "difference", "versus", "vs"]):
            query_type = "COMPARISON"
        elif any(w in lower_q for w in ["quantum", "unsupported", "unknown"]):
            query_type = "UNSUPPORTED"

        # Safe query rewriting logic (non-destructive)
        optimized_query = cleaned_query
        if query_type == "DEFINITION" and not cleaned_query.lower().startswith("define"):
            optimized_query = f"Definition and explanation of {cleaned_query}"
        elif query_type == "SUMMARY":
            optimized_query = f"Summary overview of {cleaned_query}"

        return {
            "original_query": cleaned_query,
            "optimized_query": optimized_query,
            "query_type": query_type,
            "safe_to_process": True
        }