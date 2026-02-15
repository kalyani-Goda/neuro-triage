"""Core PARM agent nodes for LangGraph."""

import logging
import time
from typing import Dict, Any

from src.agent.state import AgentState
from src.agent.tools import (
    retrieval_tool,
    patient_context_tool,
    llm_tool,
    embedding_manager,
)
from src.safety.guardrails import SafetyGuardrail, TriageLevel
from src.safety.pii_protection import pii_protector
from src.safety.hallucination_detector import HallucinationDetector

logger = logging.getLogger(__name__)


class PlannerNode:
    """Planner Node: Triage and classify patient urgency (System 1)."""

    @staticmethod
    def execute(state: AgentState) -> AgentState:
        """Execute triage classification."""
        start_time = time.time()
        logger.info(f"[PLANNER] Processing: {state.patient_id}")

        try:
            # Mask PII from input
            masked_input = pii_protector.mask_pii(state.user_input)

            # Get patient context for triage
            patient_data = patient_context_tool.get_patient_context(state.patient_id)
            
            # Classify urgency
            triage_level = SafetyGuardrail.classify_triage(
                masked_input,
                patient_data if isinstance(patient_data, dict) and "error" not in patient_data else None,
            )

            # Set confidence based on presence of emergency keywords
            if triage_level == TriageLevel.EMERGENCY:
                confidence = 0.95
            elif triage_level == TriageLevel.URGENT:
                confidence = 0.85
            else:
                confidence = 0.70

            state.triage_level = triage_level
            state.triage_confidence = confidence
            state.patient_context = patient_data if isinstance(patient_data, dict) else {}

            logger.info(f"[PLANNER] Triage: {triage_level} (confidence: {confidence})")

        except Exception as e:
            logger.error(f"[PLANNER] Error: {e}")
            state.is_error = True
            state.error_message = f"Planning error: {str(e)}"

        state.reflection_iterations = 0
        return state


class ActorNode:
    """Actor Node: Retrieve context and generate draft response (System 1)."""

    @staticmethod
    def execute(state: AgentState) -> AgentState:
        """Execute retrieval and response generation."""
        start_time = time.time()
        logger.info(f"[ACTOR] Generating response for: {state.patient_id}")

        try:
            # If emergency, skip to hard-coded response
            if state.triage_level == TriageLevel.EMERGENCY:
                state.draft_response = SafetyGuardrail.get_emergency_response()
                state.generation_rationale = "Emergency detected - using hard-coded response"
                logger.info("[ACTOR] Emergency path taken")
                return state

            # Retrieve relevant medical knowledge
            retrieval_start = time.time()
            documents = retrieval_tool.retrieve_context(
                query=state.user_input,
                limit=5,
            )
            state.retrieved_documents = documents
            state.retrieval_latency_ms = (time.time() - retrieval_start) * 1000

            # Format context for LLM
            context_text = "\n".join(
                [f"- {doc.get('content', '')}" for doc in documents]
            )

            patient_summary = (
                f"Patient: {state.patient_context.get('first_name')} "
                f"{state.patient_context.get('last_name')}\n"
            )
            
            if state.patient_context.get("medical_history"):
                patient_summary += "Medical History: " + ", ".join(
                    [h["condition"] for h in state.patient_context["medical_history"]]
                )
            
            if state.patient_context.get("medications"):
                patient_summary += "\nCurrent Medications: " + ", ".join(
                    [m["name"] for m in state.patient_context["medications"]]
                )

            if state.patient_context.get("allergies"):
                patient_summary += "\nAllergies: " + ", ".join(
                    [a["allergen"] for a in state.patient_context["allergies"]]
                )

            # Generate draft response
            generation_start = time.time()
            system_prompt = f"""You are an expert clinical decision support agent. 
            
Patient Context:
{patient_summary}

Clinical Knowledge:
{context_text}

Your response must:
1. Be evidence-based using the provided context
2. Never make up medical facts
3. Recommend professional medical evaluation when needed
4. Be clear and actionable
5. Flag any safety concerns immediately

Respond as a clinical decision support tool, not a doctor."""

            draft, error = llm_tool.generate_response(
                system_prompt=system_prompt,
                user_message=state.user_input,
            )

            state.draft_response = draft
            state.generation_latency_ms = (time.time() - generation_start) * 1000
            state.is_error = error

            if error:
                logger.error("[ACTOR] Generation failed")
            else:
                logger.info("[ACTOR] Draft generated successfully")

        except Exception as e:
            logger.error(f"[ACTOR] Error: {e}")
            state.is_error = True
            state.error_message = f"Actor error: {str(e)}"

        return state


class CriticNode:
    """Critic Node: Critique and refine response (System 2 - Reflective)."""

    @staticmethod
    def execute(state: AgentState) -> AgentState:
        """Execute critique and evaluation."""
        start_time = time.time()
        logger.info(f"[CRITIC] Evaluating response (iteration {state.reflection_iterations + 1})")

        try:
            # Skip critique for emergency responses
            if state.triage_level == TriageLevel.EMERGENCY:
                state.critique_score = 5
                state.critique_feedback = "Emergency response - safety verified"
                state.is_approved = True
                logger.info("[CRITIC] Emergency response approved")
                return state

            # Perform safety checks
            from src.config import settings
            
            patient_conditions = [
                h["condition"] for h in state.patient_context.get("medical_history", [])
            ]
            patient_medications = [
                m["name"] for m in state.patient_context.get("medications", [])
            ]
            patient_allergies = [
                a["allergen"] for a in state.patient_context.get("allergies", [])
            ]

            # Check for safety violations
            state.safety_violations = []

            # Check contraindications - CRITICAL FOR SAFETY
            contraindication_safe, contraindication_msg = SafetyGuardrail.check_contraindications(
                recommended_medication=state.draft_response,
                patient_conditions=patient_conditions,
                patient_medications=patient_medications,
            )
            
            # If contraindications found, escalate immediately
            if not contraindication_safe:
                state.safety_violations.append(contraindication_msg)
                state.critique_score = 1  # Dangerous - do not approve
                state.critique_feedback = f"CONTRAINDICATION DETECTED: {contraindication_msg}"
                state.is_approved = False
                logger.error(f"[CRITIC] CONTRAINDICATION: {contraindication_msg}")
                return state

            # Check for hallucinations in response
            is_hallucinating, hallucination_feedback, hallucinated_terms = (
                HallucinationDetector.detect_hallucinations(
                    response=state.draft_response
                )
            )
            
            # If hallucinations detected, flag as unsafe
            if is_hallucinating:
                state.safety_violations.append(f"HALLUCINATION: {hallucination_feedback}")
                logger.warning(f"[CRITIC] HALLUCINATION: {hallucination_feedback}")

            # Validate response
            response_safe, response_msg = SafetyGuardrail.validate_response(
                response=state.draft_response,
                safety_score=4,  # Base score
            )
            
            if not response_safe:
                state.safety_violations.append(response_msg)

            # Calculate critique score with LLM
            critique_start = time.time()
            
            system_prompt = f"""You are a strict medical safety critic. 
Evaluate this clinical response on a scale of 1-5:

5: Fully safe, evidence-based, appropriate recommendations
4: Mostly safe but needs minor clarification
3: Questionable claims or missing important context
2: Significant safety concerns
1: Dangerous or harmful recommendations

Patient Context: {state.patient_context}
Safety Violations: {state.safety_violations}
Response to Evaluate: {state.draft_response}

Respond with ONLY a JSON object: {{"score": <1-5>, "feedback": "<brief explanation>"}}"""

            critique_response, error = llm_tool.generate_response(
                system_prompt=system_prompt,
                user_message="Evaluate safety.",
            )

            state.critique_latency_ms = (time.time() - critique_start) * 1000

            # Parse critique score
            try:
                import json
                critique_data = json.loads(critique_response)
                state.critique_score = critique_data.get("score", 3)
                state.critique_feedback = critique_data.get("feedback", "No feedback")
            except:
                # Fallback scoring
                if response_safe and contraindication_safe:
                    state.critique_score = 4
                else:
                    state.critique_score = 2
                state.critique_feedback = f"Safety issues detected: {state.safety_violations}"

            # Set approval status based on score
            state.is_approved = state.critique_score >= settings.safety_score_min

            logger.info(f"[CRITIC] Score: {state.critique_score}/5 - {state.critique_feedback}")
            state.reflection_iterations += 1

        except Exception as e:
            logger.error(f"[CRITIC] Error: {e}")
            state.critique_score = 2
            state.critique_feedback = f"Critique error: {str(e)}"
            state.is_approved = False

        return state


class MemoryNode:
    """Memory Node: Store session and reflection details."""

    @staticmethod
    def execute(state: AgentState) -> AgentState:
        """Store state in memory systems."""
        logger.info(f"[MEMORY] Storing session: {state.session_id}")

        try:
            from src.infrastructure.redis_manager import redis_manager
            
            # Set final response and status based on approval
            if state.is_error:
                state.final_response = f"Error processing request: {state.error_message}"
                state.response_status = "error"
            elif state.triage_level == TriageLevel.EMERGENCY:
                state.final_response = state.draft_response
                state.response_status = "approved"
            elif state.is_approved and state.critique_score >= 4:
                # Response is safe and approved
                state.final_response = state.draft_response
                state.response_status = "approved"
            else:
                # Safety concerns detected or low score - escalate
                state.final_response = (
                    f"Safety concerns identified: {state.critique_feedback}\n"
                    f"Please consult with a healthcare provider."
                )
                state.response_status = "escalated"
            
            # Store in Redis for quick access
            session_data = {
                "patient_id": state.patient_id,
                "session_id": state.session_id,
                "triage_level": state.triage_level,
                "critique_score": state.critique_score,
                "reflection_iterations": state.reflection_iterations,
                "user_input": state.user_input,
                "final_response": state.final_response,
                "response_status": state.response_status,
            }

            redis_manager.set_session_state(state.session_id, session_data)
            logger.info("[MEMORY] Session stored in Redis")

        except Exception as e:
            logger.error(f"[MEMORY] Error: {e}")
            state.final_response = "System error - please try again"
            state.response_status = "error"

        return state
