"""Main agent interface."""

import logging
from typing import Dict, Any
from uuid import uuid4

from src.agent.workflow import parm_workflow
from src.agent.state import AgentState

logger = logging.getLogger(__name__)


class NeuroTriageAgent:
    """Main Neuro-Triage Agent interface."""

    def __init__(self):
        """Initialize the agent."""
        self.workflow = parm_workflow

    def process_query(
        self,
        patient_id: str,
        user_input: str,
        session_id: str = None,
    ) -> Dict[str, Any]:
        """
        Process a patient query through the PARM workflow.
        
        Args:
            patient_id: Unique patient identifier
            user_input: Patient's input/symptoms
            session_id: Optional session ID (generated if not provided)
            
        Returns:
            Dictionary containing:
            - final_response: The generated clinical response
            - triage_level: Urgency classification
            - critique_score: Safety score (1-5)
            - response_status: approved/escalated/error
            - metadata: Latencies and iterations
        """
        if not session_id:
            session_id = str(uuid4())

        try:
            # Prepare initial state
            state_dict = {
                "patient_id": patient_id,
                "session_id": session_id,
                "user_input": user_input,
            }

            # Execute workflow
            final_state = self.workflow.invoke(state_dict)

            # Format response
            return {
                "session_id": final_state.session_id,
                "patient_id": final_state.patient_id,
                "final_response": final_state.final_response,
                "triage_level": final_state.triage_level,
                "triage_confidence": final_state.triage_confidence,
                "critique_score": final_state.critique_score,
                "critique_feedback": final_state.critique_feedback,
                "response_status": final_state.response_status,
                "safety_violations": final_state.safety_violations,
                "reflection_iterations": final_state.reflection_iterations,
                "metadata": {
                    "total_latency_ms": final_state.total_latency_ms,
                    "retrieval_latency_ms": final_state.retrieval_latency_ms,
                    "generation_latency_ms": final_state.generation_latency_ms,
                    "critique_latency_ms": final_state.critique_latency_ms,
                },
                "success": not final_state.is_error,
                "error": final_state.error_message if final_state.is_error else None,
            }

        except Exception as e:
            logger.error(f"Agent processing failed: {e}")
            return {
                "session_id": session_id,
                "patient_id": patient_id,
                "success": False,
                "error": str(e),
                "response_status": "error",
            }


# Global agent instance
agent = NeuroTriageAgent()
