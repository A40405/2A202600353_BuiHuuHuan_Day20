"""Supervisor / router."""

from multi_agent_research_lab.agents.base import BaseAgent
from multi_agent_research_lab.core.config import get_settings
from multi_agent_research_lab.core.state import ResearchState


class SupervisorAgent(BaseAgent):
    """Decides which worker should run next and when to stop."""

    name = "supervisor"

    def run(self, state: ResearchState) -> ResearchState:
        """Update `state.route_history` with the next route."""

        settings = get_settings()
        if state.iteration >= settings.max_iterations:
            route = "writer" if state.final_answer is None else "done"
        elif state.final_answer:
            route = "done"
        elif state.research_notes is None:
            route = "researcher"
        elif state.analysis_notes is None:
            route = "analyst"
        else:
            route = "writer"

        state.record_route(route)
        state.add_trace_event(
            "supervisor.route",
            {
                "route": route,
                "iteration": state.iteration,
                "has_research": state.research_notes is not None,
                "has_analysis": state.analysis_notes is not None,
                "has_final": state.final_answer is not None,
            },
        )
        return state
