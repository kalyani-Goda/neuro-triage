"""
PHASE 7 — Agent Evaluation Script
Run comprehensive evaluation against benchmark datasets
Generates paper-style evaluation report with metrics, latency, safety scores
"""

import sys
import os
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

import asyncio
import logging
import time
import uuid
from datetime import datetime
from typing import Optional

from src.config import Settings
from src.agent.workflow import PARMGraphWorkflow
from src.agent.nodes import TriageLevel
from src.agent.state import AgentState
from scripts.evaluation_report import EvaluationReport

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def create_evaluation_state(patient_id: str, user_input: str, patient_context: dict = None) -> dict:
    """Create a properly formatted state for the workflow."""
    return {
        "patient_id": patient_id,
        "session_id": str(uuid.uuid4()),
        "user_input": user_input,
        "patient_context": patient_context or {},
        "triage_level": TriageLevel.ROUTINE,
        "triage_confidence": 0.0,
        "retrieved_documents": [],
        "draft_response": None,
        "generation_rationale": None,
        "critique_score": 0,
        "critique_feedback": None,
        "is_approved": False,
        "is_error": False,
        "error_message": "",
        "final_response": "",
        "response_status": "pending",
        "reflection_iterations": 0,
        "reflection_history": [],
    }


async def evaluate_agent():
    """Run comprehensive agent evaluation."""
    settings = Settings()
    workflow = PARMGraphWorkflow()
    report = EvaluationReport(settings, results_dir="results")

    print("\n" + "=" * 70)
    print("NEURO-TRIAGE EVALUATION SUITE")
    print("=" * 70)
    print(f"Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()

    # ========================================================================
    # PHASE 7.1: TRIAGE BENCHMARK EVALUATION
    # ========================================================================
    print("\n[PHASE 7.1] TRIAGE BENCHMARK EVALUATION")
    print("-" * 70)
    print(f"Running {len(report.MEDQA_BENCHMARK)} benchmark cases...")
    print()

    triage_passed = 0
    for case in report.MEDQA_BENCHMARK:
        try:
            logger.info(f"Evaluating: {case['id']} ({case['category']})")

            # Create properly formatted state
            state = create_evaluation_state(
                patient_id="faf83fb0-a2a1-4b8d-bb21-470cdbf8d60f",
                user_input=case["input"],
                patient_context={
                    "name": "Benchmark Patient",
                    "conditions": [],
                    "medications": [],
                    "allergies": [],
                }
            )

            # Time the workflow execution
            start_time = time.time()
            try:
                result_obj = workflow.invoke(state)
                end_time = time.time()
                
                # Convert AgentState to dict if needed
                if hasattr(result_obj, '__dict__'):
                    result = vars(result_obj)
                else:
                    result = result_obj

                latency_ms = (end_time - start_time) * 1000
                report.add_performance_data(
                    response_time_ms=latency_ms,
                    reflection_iterations=result.get("reflection_iterations", 0),
                    token_usage=0,  # Would need to track token usage
                )

                # Check triage accuracy
                expected_triage = case["expected_triage"]
                predicted_triage = result.get("triage_level")

                report.add_triage_result(predicted_triage, expected_triage)

                if predicted_triage == expected_triage:
                    triage_passed += 1
                    status = "✅ PASS"
                else:
                    status = "❌ FAIL"

                print(
                    f"{status} | {case['id']:20} | "
                    f"Expected: {expected_triage.value:8} | "
                    f"Got: {predicted_triage.value if predicted_triage else 'NONE':8} | "
                    f"Latency: {latency_ms:6.0f}ms"
                )

            except Exception as e:
                logger.error(f"Workflow execution failed: {e}")
                print(f"❌ ERROR | {case['id']:20} | Exception: {str(e)[:40]}")
                report.add_performance_data(response_time_ms=0, reflection_iterations=0, token_usage=0)

        except Exception as e:
            logger.error(f"Benchmark case {case['id']} failed: {e}")

    print()
    print(f"Triage Benchmark: {triage_passed}/{len(report.MEDQA_BENCHMARK)} passed")
    print()

    # ========================================================================
    # PHASE 7.2: SAFETY BENCHMARK EVALUATION
    # ========================================================================
    print("\n[PHASE 7.2] SAFETY BENCHMARK EVALUATION")
    print("-" * 70)
    print(f"Running {len(report.SAFETY_TEST_CASES)} safety test cases...")
    print()

    safety_passed = 0
    for case in report.SAFETY_TEST_CASES:
        try:
            logger.info(f"Evaluating: {case['id']}")

            # Create properly formatted state
            state = create_evaluation_state(
                patient_id="7204522b-7a5b-4b23-a488-829311698678",
                user_input=case["input"],
                patient_context={
                    "name": "Benchmark Patient",
                    "conditions": ["Diabetes"] if "diabetes" in case["input"].lower() else [],
                    "medications": ["Naproxen", "Metformin", "Warfarin"],
                    "allergies": ["Aspirin"],
                }
            )

            start_time = time.time()
            try:
                result_obj = workflow.invoke(state)
                end_time = time.time()
                
                # Convert AgentState to dict if needed
                if hasattr(result_obj, '__dict__'):
                    result = vars(result_obj)
                else:
                    result = result_obj

                latency_ms = (end_time - start_time) * 1000
                report.add_performance_data(
                    response_time_ms=latency_ms,
                    reflection_iterations=result.get("reflection_iterations", 0),
                    token_usage=0,
                )

                # Check if safety response is appropriate
                is_approved = result.get("response_status") == "approved"
                has_contraindication = case.get("contraindication") is not None

                report.add_safety_result(
                    is_approved=is_approved,
                    has_contraindication=has_contraindication,
                    has_hallucination=False,
                    has_error=result.get("is_error", False),
                )

                # Determine if result matches expectation
                expected_escalation = case["expected_escalation"]
                actual_escalation = not is_approved
                passed = actual_escalation == expected_escalation

                if passed:
                    safety_passed += 1
                    status = "✅ PASS"
                else:
                    status = "❌ FAIL"

                escalation_str = "Escalated" if actual_escalation else "Approved"
                expected_str = "Escalated" if expected_escalation else "Approved"

                print(
                    f"{status} | {case['id']:15} | "
                    f"Expected: {expected_str:10} | "
                    f"Got: {escalation_str:10} | "
                    f"Score: {result.get('critique_score', 0):.1f}/5"
                )

            except Exception as e:
                logger.error(f"Workflow execution failed: {e}")
                print(f"❌ ERROR | {case['id']:15} | Exception: {str(e)[:40]}")
                report.add_safety_result(
                    is_approved=False,
                    has_contraindication=False,
                    has_hallucination=False,
                    has_error=True,
                )

        except Exception as e:
            logger.error(f"Safety case {case['id']} failed: {e}")

    print()
    print(f"Safety Benchmark: {safety_passed}/{len(report.SAFETY_TEST_CASES)} passed")
    print()

    # ========================================================================
    # PHASE 7.3: HALLUCINATION DETECTION
    # ========================================================================
    print("\n[PHASE 7.3] HALLUCINATION DETECTION BENCHMARK")
    print("-" * 70)
    print(f"Running {len(report.HALLUCINATION_TEST_CASES)} hallucination tests...")
    print()

    halluc_passed = 0
    for case in report.HALLUCINATION_TEST_CASES:
        try:
            logger.info(f"Evaluating: {case['id']}")

            # Create properly formatted state
            state = create_evaluation_state(
                patient_id="7b4ebc74-f40c-4967-99a1-389ea492d931",
                user_input=case["input"],
                patient_context={
                    "name": "Benchmark Patient",
                    "conditions": [],
                    "medications": [],
                    "allergies": [],
                }
            )

            start_time = time.time()
            try:
                result_obj = workflow.invoke(state)
                end_time = time.time()
                
                # Convert AgentState to dict if needed
                if hasattr(result_obj, '__dict__'):
                    result = vars(result_obj)
                else:
                    result = result_obj

                latency_ms = (end_time - start_time) * 1000
                report.add_performance_data(
                    response_time_ms=latency_ms,
                    reflection_iterations=result.get("reflection_iterations", 0),
                    token_usage=0,
                )

                # For hallucination detection, we expect an error status
                is_error = result.get("is_error", False)
                passed = is_error  # Hallucination test should result in error/rejection

                if passed:
                    halluc_passed += 1
                    status = "✅ PASS"
                else:
                    status = "❌ FAIL"

                error_str = "Rejected (Error)" if is_error else "Accepted"
                print(
                    f"{status} | {case['id']:15} | "
                    f"Status: {error_str:20} | "
                    f"Latency: {latency_ms:6.0f}ms"
                )

                report.add_safety_result(
                    is_approved=result.get("response_status") == "approved",
                    has_contraindication=False,
                    has_hallucination=not is_error,
                    has_error=is_error,
                )

            except Exception as e:
                logger.error(f"Workflow execution failed: {e}")
                print(f"❌ ERROR | {case['id']:15} | Exception: {str(e)[:40]}")
                report.add_safety_result(
                    is_approved=False,
                    has_contraindication=False,
                    has_hallucination=False,
                    has_error=True,
                )

        except Exception as e:
            logger.error(f"Hallucination case {case['id']} failed: {e}")

    print()
    print(f"Hallucination Detection: {halluc_passed}/{len(report.HALLUCINATION_TEST_CASES)} passed")
    print()

    # ========================================================================
    # PHASE 7.4: METRICS SUMMARY & REPORT GENERATION
    # ========================================================================
    print("\n[PHASE 7.4] QUANTITATIVE METRICS SUMMARY")
    print("-" * 70)

    # Triage metrics
    print("\n### Triage Classification Metrics")
    print(f"  Recall (Sensitivity): {report.triage_metrics.recall:.1%}")
    print(f"  Precision:            {report.triage_metrics.precision:.1%}")
    print(f"  F1-Score:             {report.triage_metrics.f1_score:.3f}")
    print(f"  Specificity:          {report.triage_metrics.specificity:.1%}")

    # Safety metrics
    print("\n### Safety & Approval Metrics")
    print(f"  Total Queries:        {report.safety_metrics.total_queries}")
    print(f"  Approved:             {report.safety_metrics.approved_responses} ({report.safety_metrics.approval_rate:.1%})")
    print(f"  Escalated:            {report.safety_metrics.escalated_responses} ({report.safety_metrics.escalation_rate:.1%})")
    print(f"  Errors:               {report.safety_metrics.error_responses} ({report.safety_metrics.error_rate:.1%})")
    print(f"  Contraindications Caught: {report.safety_metrics.contraindications_caught}")
    print(f"  Hallucinations Detected:  {report.safety_metrics.hallucinations_detected}")

    # Performance metrics
    print("\n### Performance & Latency (milliseconds)")
    if report.performance_metrics.response_times:
        print(f"  Mean Latency:         {report.performance_metrics.mean_latency_ms:.1f}ms")
        print(f"  Median Latency:       {report.performance_metrics.median_latency_ms:.1f}ms")
        print(f"  P95 Latency:          {report.performance_metrics.p95_latency_ms:.1f}ms")
        print(f"  P99 Latency:          {report.performance_metrics.p99_latency_ms:.1f}ms")
        print(f"  Mean Reflection Iter: {report.performance_metrics.mean_reflection_iterations:.2f}")
    else:
        print("  (No performance data collected)")

    # Generate reports
    print("\n" + "-" * 70)
    print("[PHASE 7.5] GENERATING EVALUATION REPORTS")
    print("-" * 70)

    report_paths = report.save_reports()
    print(f"\n✅ Reports generated:")
    for format_name, path in report_paths.items():
        print(f"  - {format_name.upper()}: {path}")

    print("\n" + "=" * 70)
    print("EVALUATION COMPLETE")
    print("=" * 70)
    print()


if __name__ == "__main__":
    asyncio.run(evaluate_agent())
