"""Advanced agent enhancements and extensions."""

import logging
from typing import Dict, Any, List, Optional
from enum import Enum

logger = logging.getLogger(__name__)


class ResponseConfidenceLevel(Enum):
    """Confidence levels for responses."""

    HIGH = 5  # Fully confident
    MEDIUM_HIGH = 4
    MEDIUM = 3
    MEDIUM_LOW = 2
    LOW = 1  # Not confident


class EnhancedCriticAgent:
    """
    Enhanced Critic Agent with advanced evaluation capabilities.
    
    Enhancements:
    1. Multi-factor safety scoring
    2. Confidence calibration
    3. Explainability scores
    4. Evidence tracking
    """

    # Safety factor weights
    SAFETY_WEIGHTS = {
        "factual_accuracy": 0.25,
        "contraindication_check": 0.25,
        "evidence_based": 0.20,
        "appropriate_escalation": 0.15,
        "language_safety": 0.15,
    }

    @staticmethod
    def compute_multifactor_score(factors: Dict[str, float]) -> int:
        """
        Compute safety score from multiple factors.
        
        Args:
            factors: Dictionary of factor_name -> score (0-1)
            
        Returns:
            Integrated score (1-5)
        """
        weighted_score = sum(
            factors.get(factor, 0) * weight
            for factor, weight in EnhancedCriticAgent.SAFETY_WEIGHTS.items()
        )
        
        # Convert 0-1 scale to 1-5 scale
        return max(1, min(5, int(weighted_score * 5)))

    @staticmethod
    def assess_confidence_calibration(
        model_confidence: float,
        actual_safety: float,
    ) -> float:
        """
        Assess model confidence calibration.
        
        Model should be confident when response is actually safe.
        Penalize overconfidence on unsafe responses.
        """
        if model_confidence > 0.8 and actual_safety < 0.6:
            # Overconfident - penalty
            return 0.5
        elif model_confidence < 0.5 and actual_safety > 0.8:
            # Underconfident - minor penalty
            return 0.8
        else:
            # Well calibrated
            return 1.0

    @staticmethod
    def extract_evidence(response: str, retrieved_docs: List[Dict]) -> Dict[str, Any]:
        """Extract evidence supporting the response."""
        evidence = {
            "sources_cited": [],
            "evidence_count": 0,
            "hallucinations": [],
        }

        for doc in retrieved_docs:
            doc_content = doc.get("content", "").lower()
            response_lower = response.lower()

            # Simple heuristic: check if key terms from doc appear in response
            key_terms = doc_content.split()[:10]
            found_terms = [t for t in key_terms if t in response_lower]

            if found_terms:
                evidence["sources_cited"].append(doc.get("title", "Unknown"))
                evidence["evidence_count"] += len(found_terms)

        return evidence


class AdaptiveRefinementStrategy:
    """
    Adaptive refinement strategy based on failure modes.
    
    Instead of generic retry, tailor refinement prompts to specific issues.
    """

    FAILURE_MODES = {
        "hallucination": "The response contains unsupported claims. Regenerate using ONLY information from provided documents.",
        "contraindication": "The response ignores patient allergies/conditions. Check contraindications and modify recommendation.",
        "incomplete": "The response is too brief. Provide detailed explanation with evidence.",
        "unsafe_language": "The response contains dangerous language. Rewrite to properly escalate to healthcare provider.",
    }

    @staticmethod
    def diagnose_failure(critique_feedback: str) -> Optional[str]:
        """Diagnose the failure mode from critique feedback."""
        feedback_lower = critique_feedback.lower()

        for mode in AdaptiveRefinementStrategy.FAILURE_MODES:
            if mode in feedback_lower:
                return mode

        return None

    @staticmethod
    def get_refinement_prompt(failure_mode: str) -> str:
        """Get tailored refinement prompt for the failure mode."""
        return AdaptiveRefinementStrategy.FAILURE_MODES.get(
            failure_mode,
            "Improve the response quality.",
        )


class MemoryContextBuilder:
    """
    Build richer context from conversation memory.
    
    Improvements:
    1. Long-term patient patterns
    2. Previous query similarity detection
    3. Context aggregation from multiple sessions
    """

    @staticmethod
    def extract_conversation_patterns(
        conversation_history: List[Dict[str, str]],
    ) -> Dict[str, Any]:
        """Extract patterns from conversation history."""
        patterns = {
            "recurring_symptoms": [],
            "medication_changes": [],
            "triage_escalations": [],
            "avg_sessions_per_week": 0,
        }

        # Implementation would analyze history
        # This is a placeholder for concept

        return patterns

    @staticmethod
    def detect_context_drift(
        current_session_context: Dict,
        historical_context: Dict,
    ) -> float:
        """Detect if patient context has significantly changed.
        Detect if patient context has significantly changed.
        Returns drift score (0-1): 0 = no change, 1 = major change
        """
        # Placeholder: would compute semantic similarity
        return 0.0


class ExplainabilityEnhancer:
    """
    Add explainability to agent decisions.
    
    Features:
    1. Reasoning traces
    2. Decision trees
    3. Counterfactual explanations
    """

    @staticmethod
    def generate_reasoning_trace(state) -> str:
        """Generate human-readable reasoning trace."""
        trace = f"""
## Reasoning Trace

**Input**: {state.user_input}

**Step 1 - Triage**: 
- Identified triage level: {state.triage_level}
- Confidence: {state.triage_confidence:.1%}
- Reasoning: {state.generation_rationale}

**Step 2 - Retrieval**:
- Retrieved {len(state.retrieved_documents)} relevant documents
- Top match: {state.retrieved_documents[0].get('title', 'N/A') if state.retrieved_documents else 'None'}

**Step 3 - Generation**:
- Generated draft response
- Length: {len(state.draft_response)} characters

**Step 4 - Critique**:
- Safety score: {state.critique_score}/5
- Feedback: {state.critique_feedback}
- Violations: {', '.join(state.safety_violations) or 'None'}

**Final Decision**:
- Status: {state.response_status}
- Iterations: {state.reflection_iterations}
"""
        return trace

    @staticmethod
    def generate_decision_rationale(state) -> str:
        """Generate decision rationale for clinician review."""
        rationale = f"""
This response was generated through the following process:

1. **Symptom Classification**: The input was classified as '{state.triage_level}' urgency
   - Emergency protocol activated: {state.triage_level == 'emergency'}

2. **Knowledge Retrieval**: Medical knowledge base was queried to find relevant guidelines

3. **Response Generation**: A clinical response was generated based on:
   - Patient medical history: {len(state.patient_context.get('medical_history', []))} conditions
   - Current medications: {len(state.patient_context.get('medications', []))} drugs
   - Known allergies: {len(state.patient_context.get('allergies', []))} allergies

4. **Safety Review**: Response was scored {state.critique_score}/5 on safety criteria:
   - Factual accuracy: Checked against retrieval
   - Contraindication check: Verified against patient profile
   - Appropriate escalation: Flagged urgent cases

5. **Recommendation**: {state.response_status.upper()}
   - {'This response meets safety thresholds.' if state.critique_score >= 4 else 'This response may require expert review.'}
"""
        return rationale


class ObservabilityEnhancements:
    """
    Enhanced observability and monitoring.
    """

    @staticmethod
    def compute_quality_metrics(results: List[Dict]) -> Dict[str, float]:
        """Compute quality metrics across multiple results."""
        if not results:
            return {}

        metrics = {
            "avg_safety_score": sum(r.get("critique_score", 0) for r in results) / len(results),
            "approval_rate": sum(1 for r in results if r.get("response_status") == "approved") / len(results),
            "escalation_rate": sum(1 for r in results if r.get("response_status") == "escalated") / len(results),
            "refinement_rate": sum(1 for r in results if r.get("reflection_iterations", 0) > 0) / len(results),
            "avg_latency_ms": sum(r.get("metadata", {}).get("total_latency_ms", 0) for r in results) / len(results),
        }

        return metrics

    @staticmethod
    def identify_failure_patterns(results: List[Dict]) -> List[str]:
        """Identify patterns in failed or low-quality responses."""
        patterns = []

        low_score_responses = [r for r in results if r.get("critique_score", 5) < 3]

        if low_score_responses:
            patterns.append(f"High failure rate: {len(low_score_responses)}/{len(results)}")

        escalated = [r for r in results if r.get("response_status") == "escalated"]
        if len(escalated) > len(results) * 0.3:
            patterns.append("Excessive escalations - may indicate overly conservative critique")

        high_latency = [r for r in results if r.get("metadata", {}).get("total_latency_ms", 0) > 5000]
        if high_latency:
            patterns.append(f"High latency in {len(high_latency)}/{len(results)} responses")

        return patterns
