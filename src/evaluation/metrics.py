"""Evaluation metrics for Neuro-Triage."""

import logging
from typing import List, Dict, Any, Tuple
import json

logger = logging.getLogger(__name__)


class EvaluationMetrics:
    """Compute evaluation metrics for clinical responses."""

    @staticmethod
    def hallucination_rate(responses: List[Dict[str, Any]]) -> float:
        """
        Calculate hallucination rate using Ragas faithfulness metric.
        
        In practice, you'd use ragas library:
        from ragas.metrics import faithfulness
        
        For now, we'll use simple heuristic checking.
        """
        hallucination_count = 0

        for response in responses:
            # Check for unsupported claims (simplified)
            if "may cause" in response.get("response", "").lower():
                hallucination_count += 1
            if "always leads to" in response.get("response", "").lower():
                hallucination_count += 1

        return hallucination_count / len(responses) if responses else 0

    @staticmethod
    def triage_recall(predictions: List[str], ground_truth: List[str]) -> float:
        """
        Calculate recall for emergency triage classification.
        
        Metric: Out of all true emergency cases, how many did we catch?
        """
        true_positives = 0
        false_negatives = 0

        for pred, truth in zip(predictions, ground_truth):
            if truth == "emergency":
                if pred == "emergency":
                    true_positives += 1
                else:
                    false_negatives += 1

        total_emergencies = true_positives + false_negatives
        return true_positives / total_emergencies if total_emergencies > 0 else 0

    @staticmethod
    def triage_precision(predictions: List[str], ground_truth: List[str]) -> float:
        """
        Calculate precision for emergency triage classification.
        
        Metric: Out of all cases we flagged as emergency, how many were correct?
        """
        true_positives = 0
        false_positives = 0

        for pred, truth in zip(predictions, ground_truth):
            if pred == "emergency":
                if truth == "emergency":
                    true_positives += 1
                else:
                    false_positives += 1

        total_predicted_emergency = true_positives + false_positives
        return true_positives / total_predicted_emergency if total_predicted_emergency > 0 else 0

    @staticmethod
    def latency_metrics(response_times: List[float]) -> Dict[str, float]:
        """Compute latency statistics."""
        if not response_times:
            return {}

        return {
            "mean_latency_ms": sum(response_times) / len(response_times),
            "median_latency_ms": sorted(response_times)[len(response_times) // 2],
            "max_latency_ms": max(response_times),
            "min_latency_ms": min(response_times),
            "p95_latency_ms": sorted(response_times)[int(len(response_times) * 0.95)],
            "p99_latency_ms": sorted(response_times)[int(len(response_times) * 0.99)],
        }

    @staticmethod
    def safety_score_distribution(scores: List[int]) -> Dict[str, Any]:
        """Analyze distribution of safety scores."""
        if not scores:
            return {}

        score_counts = {1: 0, 2: 0, 3: 0, 4: 0, 5: 0}
        for score in scores:
            score_counts[min(5, max(1, score))] += 1

        return {
            "score_distribution": score_counts,
            "mean_score": sum(scores) / len(scores),
            "approval_rate": sum(1 for s in scores if s >= 4) / len(scores),
        }

    @staticmethod
    def reflection_iteration_analysis(iterations: List[int]) -> Dict[str, Any]:
        """Analyze reflection iterations."""
        if not iterations:
            return {}

        return {
            "mean_iterations": sum(iterations) / len(iterations),
            "max_iterations": max(iterations),
            "queries_needing_refinement": sum(1 for i in iterations if i > 0),
            "refinement_rate": sum(1 for i in iterations if i > 0) / len(iterations),
        }


class BenchmarkEvaluator:
    """Evaluate agent on benchmark datasets."""

    def __init__(self):
        """Initialize evaluator."""
        self.metrics = EvaluationMetrics()

    def evaluate_medqa_subset(
        self,
        agent,
        questions: List[Dict[str, str]],
    ) -> Dict[str, Any]:
        """
        Evaluate agent on MedQA questions.
        
        Expected question format:
        {
            "patient_id": "...",
            "question": "...",
            "expected_triage": "emergency|urgent|routine"
        }
        """
        predictions = []
        ground_truths = []
        response_times = []

        for q in questions:
            try:
                import time
                start = time.time()

                result = agent.process_query(
                    patient_id=q["patient_id"],
                    user_input=q["question"],
                )

                elapsed = (time.time() - start) * 1000

                predictions.append(result.get("triage_level", "routine"))
                ground_truths.append(q.get("expected_triage", "routine"))
                response_times.append(elapsed)

            except Exception as e:
                logger.error(f"Evaluation error: {e}")
                predictions.append("routine")
                ground_truths.append(q.get("expected_triage", "routine"))

        # Compute metrics
        return {
            "triage_recall": self.metrics.triage_recall(predictions, ground_truths),
            "triage_precision": self.metrics.triage_precision(predictions, ground_truths),
            "latency_metrics": self.metrics.latency_metrics(response_times),
            "predictions": predictions,
            "ground_truth": ground_truths,
        }

    def evaluate_safety(self, agent, test_cases: List[Dict[str, str]]) -> Dict[str, Any]:
        """
        Evaluate agent safety on adversarial test cases.
        """
        safety_scores = []
        violations_count = 0

        for case in test_cases:
            result = agent.process_query(
                patient_id=case.get("patient_id", "test_001"),
                user_input=case["query"],
            )

            safety_scores.append(result.get("critique_score", 0))
            violations_count += len(result.get("safety_violations", []))

        return {
            "safety_scores": self.metrics.safety_score_distribution(safety_scores),
            "total_violations": violations_count,
            "average_violations_per_query": violations_count / len(test_cases) if test_cases else 0,
        }
