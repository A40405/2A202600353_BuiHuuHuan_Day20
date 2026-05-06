"""Analyst agent."""
from multi_agent_research_lab.agents.base import BaseAgent
from multi_agent_research_lab.core.schemas import AgentName, AgentResult
from multi_agent_research_lab.core.state import ResearchState
from multi_agent_research_lab.services.llm_client import LLMClient


class AnalystAgent(BaseAgent):
    """Turns research notes into structured insights."""

    name = "analyst"

    def __init__(self, llm_client: LLMClient | None = None) -> None:
        self.llm_client = llm_client or LLMClient()

    def run(self, state: ResearchState) -> ResearchState:
        """Populate `state.analysis_notes` using LLM."""

        if not state.research_notes:
            state.errors.append("Analyst ran before research notes were available.")
            state.analysis_notes = "Insufficient evidence: no research notes were provided."
        else:
            response = self.llm_client.complete(
                system_prompt=(
                    "You are the Analyst agent. Your job is to extract key claims, "
                    "identify tradeoffs, and find evidence gaps from research notes. "
                    "Provide structured insights. Do not think step by step. /no_think"
                ),
                user_prompt=f"Research Notes:\n{state.research_notes}\n\nAnalyze the findings for the query: {state.request.query}",
            )
            state.analysis_notes = response.content

        state.agent_results.append(
            AgentResult(agent=AgentName.ANALYST, content=state.analysis_notes, metadata={})
        )
        state.add_trace_event("analyst.complete", {"has_errors": bool(state.errors)})
        return state
