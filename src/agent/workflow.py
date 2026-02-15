"""LangGraph PARM workflow orchestration."""

from langgraph.graph import StateGraph, END
from typing import Literal
from dataclasses import asdict, fields
import logging

from src.agent.state import AgentState
from src.agent.nodes import PlannerNode, ActorNode, CriticNode, MemoryNode
from src.config import settings

logger = logging.getLogger(__name__)


class PARMGraphWorkflow:
    """
    PARM (Planning, Action, Reflection, Memory) Workflow using LangGraph.
    
    Flow:
    1. Planner (Triage): Classify urgency
    2. Actor (Retrieval & Generation): Generate draft response
    3. Critic (Reflection): Evaluate safety
    4. Conditional: If safe, return; else refine
    5. Memory: Store session
    """

    def __init__(self):
        """Initialize the PARM workflow graph."""
        self.graph = self._build_graph()
        self.compiled_graph = self.graph.compile()

    def _build_graph(self) -> StateGraph:
        """Build the LangGraph state graph."""
        workflow = StateGraph(AgentState)

        # Wrapper functions to handle dict <-> AgentState conversion
        def planner_wrapper(state_dict):
            state = AgentState(**state_dict) if isinstance(state_dict, dict) else state_dict
            result = PlannerNode.execute(state)
            return asdict(result) if isinstance(result, AgentState) else result

        def actor_wrapper(state_dict):
            state = AgentState(**state_dict) if isinstance(state_dict, dict) else state_dict
            result = ActorNode.execute(state)
            return asdict(result) if isinstance(result, AgentState) else result

        def critic_wrapper(state_dict):
            state = AgentState(**state_dict) if isinstance(state_dict, dict) else state_dict
            result = CriticNode.execute(state)
            return asdict(result) if isinstance(result, AgentState) else result

        def memory_wrapper(state_dict):
            state = AgentState(**state_dict) if isinstance(state_dict, dict) else state_dict
            result = MemoryNode.execute(state)
            return asdict(result) if isinstance(result, AgentState) else result

        # Add nodes with wrappers
        workflow.add_node("planner", planner_wrapper)
        workflow.add_node("actor", actor_wrapper)
        workflow.add_node("critic", critic_wrapper)
        workflow.add_node("memory", memory_wrapper)

        # Add edges
        workflow.set_entry_point("planner")
        workflow.add_edge("planner", "actor")
        workflow.add_edge("actor", "critic")

        # Conditional edge from critic to refinement or end
        workflow.add_conditional_edges(
            "critic",
            self._should_refine,
            {
                "refine": "actor",  # Retry generation with critique feedback
                "approve": "memory",  # Response is safe
            },
        )

        workflow.add_edge("memory", END)

        return workflow

    @staticmethod
    def _should_refine(state) -> Literal["refine", "approve"]:
        """Decide whether to refine response or approve it."""
        # Convert dict to AgentState if needed
        if isinstance(state, dict):
            state = AgentState(**state)
        
        # Safety threshold
        min_score = settings.safety_score_min

        if state.is_error:
            logger.warning("Error detected, approving response as-is")
            return "approve"

        if state.triage_level == "emergency":
            logger.info("Emergency response, skipping refinement")
            return "approve"

        # CRITICAL: If contraindications detected, escalate immediately (don't refine)
        if state.safety_violations:
            logger.error(f"Safety violations detected: {state.safety_violations}")
            logger.error("Cannot refine response with contraindications - escalating")
            return "approve"  # Send to Memory node for escalation

        # Check if we've exceeded max iterations
        max_iterations = 3
        if state.reflection_iterations >= max_iterations:
            logger.warning(f"Max iterations reached ({max_iterations}), approving")
            return "approve"

        # Check safety score
        if state.critique_score >= min_score:
            logger.info(f"Safety score {state.critique_score} meets threshold")
            return "approve"
        else:
            logger.warning(
                f"Safety score {state.critique_score} below threshold {min_score}, refining"
            )
            return "refine"

    def invoke(self, state_dict: dict) -> AgentState:
        """Execute the workflow."""
        logger.info(f"[WORKFLOW] Starting for patient {state_dict.get('patient_id')}")
        
        # Execute compiled graph with dict - StateGraph handles dict internally
        result = self.compiled_graph.invoke(state_dict)
        
        # Convert result dict back to AgentState
        if isinstance(result, dict):
            final_state = AgentState(**result)
        else:
            final_state = result
        
        logger.info(
            f"[WORKFLOW] Complete - "
            f"Status: {final_state.response_status}, "
            f"Iterations: {final_state.reflection_iterations}, "
            f"Score: {final_state.critique_score}/5"
        )
        
        return final_state


# Global workflow instance
parm_workflow = PARMGraphWorkflow()
