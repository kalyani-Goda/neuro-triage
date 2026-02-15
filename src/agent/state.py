"""Agent state definition for PARM architecture."""

from dataclasses import dataclass, field
from typing import Dict, Any, List, Optional
from datetime import datetime


@dataclass
class AgentState:
    """
    State representation for the PARM (Planning, Action, Reflection, Memory) agent.
    
    This state flows through:
    1. Planning (Triage) - Classify urgency
    2. Action (Retrieval & Generation) - Draft response
    3. Reflection (Critic) - Evaluate safety
    4. Memory - Store session & learnings
    """

    # Input & Context
    patient_id: str
    session_id: str
    user_input: str
    timestamp: datetime = field(default_factory=datetime.utcnow)

    # Planning (Triage) Phase
    triage_level: Optional[str] = None  # "emergency", "urgent", "routine"
    triage_confidence: float = 0.0

    # Patient Context (from Memory)
    patient_context: Dict[str, Any] = field(default_factory=dict)
    retrieved_documents: List[Dict[str, Any]] = field(default_factory=list)

    # Action (Generation) Phase
    draft_response: Optional[str] = None
    generation_rationale: Optional[str] = None

    # Reflection (Critique) Phase
    critique_score: int = 0  # 1-5 scale
    critique_feedback: Optional[str] = None
    safety_violations: List[str] = field(default_factory=list)
    contraindication_check: bool = True
    is_approved: bool = False  # Safety approval status

    # Final Response
    final_response: Optional[str] = None
    response_status: str = "pending"  # pending, approved, rejected, escalated

    # Metadata & Tracing
    reflection_iterations: int = 0
    total_latency_ms: float = 0.0
    retrieval_latency_ms: float = 0.0
    generation_latency_ms: float = 0.0
    critique_latency_ms: float = 0.0

    # Error Handling
    error_message: Optional[str] = None
    is_error: bool = False

    def to_dict(self) -> Dict[str, Any]:
        """Convert state to dictionary."""
        return {
            "patient_id": self.patient_id,
            "session_id": self.session_id,
            "user_input": self.user_input,
            "triage_level": self.triage_level,
            "triage_confidence": self.triage_confidence,
            "patient_context": self.patient_context,
            "draft_response": self.draft_response,
            "critique_score": self.critique_score,
            "final_response": self.final_response,
            "response_status": self.response_status,
            "reflection_iterations": self.reflection_iterations,
        }
