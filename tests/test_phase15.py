import unittest
from core.query_optimizer import QueryOptimizer
from core.planner import Planner
from evaluation.rag_evaluator import RAGEvaluator

class TestPhase15(unittest.TestCase):
    def setUp(self):
        self.optimizer = QueryOptimizer()
        self.planner = Planner()

    def test_query_optimization(self):
        res = self.optimizer.analyze_and_optimize("what is normalization")
        self.assertEqual(res["query_type"], "DEFINITION")
        self.assertTrue(res["safe_to_process"])

    def test_unsupported_query_detection(self):
        res = self.optimizer.analyze_and_optimize("quantum indexing unknown")
        self.assertEqual(res["query_type"], "UNSUPPORTED")

    def test_plan_generation_and_validation(self):
        plan = self.planner.create_plan("Summarize my notes and create a task")
        validated_plan = self.planner.validate_plan(plan)
        self.assertTrue(validated_plan["is_valid"])
        self.assertGreaterEqual(len(validated_plan["steps"]), 1)

    def test_rag_evaluator_loading(self):
        evaluator = RAGEvaluator(dataset_path="evaluation/rag_dataset.json")
        self.assertGreaterEqual(len(evaluator.data), 1)

if __name__ == "__main__":
    unittest.main()