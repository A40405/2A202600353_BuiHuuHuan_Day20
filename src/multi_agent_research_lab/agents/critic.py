"""Optional critic agent for bonus work."""

from multi_agent_research_lab.agents.base import BaseAgent
from multi_agent_research_lab.core.schemas import AgentName, AgentResult
from multi_agent_research_lab.core.state import ResearchState


class CriticAgent(BaseAgent):
    """Optional fact-checking and safety-review agent."""

    name = "critic"

    def run(self, state: ResearchState) -> ResearchState:
        """Validate final answer and append findings."""

        findings: list[str] = []
        if not state.final_answer:
            findings.append("Missing final answer.")
        if state.final_answer and state.sources and "[1]" not in state.final_answer:
            findings.append("Final answer does not reference captured sources.")
        if not findings:
            findings.append("Critic check passed for basic completeness and citation presence.")

        content = "\n".join(findings)
        state.agent_results.append(
            AgentResult(agent=AgentName.CRITIC, content=content, metadata={})
        )
        state.add_trace_event("critic.complete", {"finding_count": len(findings)})
        return state
