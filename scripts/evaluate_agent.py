"""Evaluation script for benchmarking Neuro-Triage."""

import logging
import json
from datetime import datetime
from pathlib import Path

from src.agent import agent
from src.evaluation.metrics import BenchmarkEvaluator
from src.evaluation.benchmarks import MEDQA_BENCHMARK, SAFETY_TEST_CASES

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def run_evaluation():
    """Run comprehensive evaluation."""
    logger.info("=" * 60)
    logger.info("Neuro-Triage Evaluation")
    logger.info("=" * 60)
    
    evaluator = BenchmarkEvaluator()
    results = {}
    
    try:
        # 1. Triage Classification Evaluation
        logger.info("\\n[1] Triage Classification Evaluation")
        logger.info(f"Testing {len(MEDQA_BENCHMARK)} cases...")
        
        triage_results = evaluator.evaluate_medqa_subset(agent, MEDQA_BENCHMARK)
        results["triage_evaluation"] = {
            "recall": triage_results["triage_recall"],
            "precision": triage_results["triage_precision"],
            "latency_metrics": triage_results["latency_metrics"],
        }
        
        logger.info(f"✓ Triage Recall: {triage_results['triage_recall']:.2%}")
        logger.info(f"✓ Triage Precision: {triage_results['triage_precision']:.2%}")
        
        # 2. Safety Evaluation
        logger.info("\\n[2] Safety & Contraindication Evaluation")
        logger.info(f"Testing {len(SAFETY_TEST_CASES)} safety cases...")
        
        safety_results = evaluator.evaluate_safety(agent, SAFETY_TEST_CASES)
        results["safety_evaluation"] = safety_results
        
        logger.info(f"✓ Safety Score Distribution: {safety_results['safety_scores']['approval_rate']:.2%} approved")
        logger.info(f"✓ Total Safety Violations: {safety_results['total_violations']}")
        
        # Save results
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        report_path = Path(f"evaluation_report_{timestamp}.json")
        
        with open(report_path, "w") as f:
            json.dump(results, f, indent=2)
        
        logger.info(f"\\n✓ Report saved: {report_path}")
        
        # Print summary
        logger.info("\\n" + "=" * 60)
        logger.info("EVALUATION SUMMARY")
        logger.info("=" * 60)
        logger.info(f"Triage Recall: {results['triage_evaluation']['recall']:.2%}")
        logger.info(f"Safety Approval Rate: {results['safety_evaluation']['safety_scores']['approval_rate']:.2%}")
        logger.info("=" * 60)
        
    except Exception as e:
        logger.error(f"Evaluation failed: {e}")
        raise


if __name__ == "__main__":
    run_evaluation()
