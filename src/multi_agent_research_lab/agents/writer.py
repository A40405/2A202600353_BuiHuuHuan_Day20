"""Writer agent."""

from multi_agent_research_lab.agents.base import BaseAgent
from multi_agent_research_lab.core.schemas import AgentName, AgentResult
from multi_agent_research_lab.core.state import ResearchState
from multi_agent_research_lab.services.llm_client import LLMClient


class WriterAgent(BaseAgent):
    """Produces final answer from research and analysis notes."""

    name = "writer"

    def __init__(self, llm_client: LLMClient | None = None) -> None:
        self.llm_client = llm_client or LLMClient()

    def run(self, state: ResearchState) -> ResearchState:
        """Populate `state.final_answer`."""

        citations = []
        for index, source in enumerate(state.sources, start=1):
            location = source.url or "local lab corpus"
            citations.append(f"[{index}] {source.title} - {location}")

        source_section = "\n".join(citations or ["No sources were captured."])
        response = self.llm_client.complete(
            system_prompt=(
                "You are the Writer agent in a production multi-agent research system. "
                "Your goal is to synthesize research and analysis notes into a professional final answer. "
                "Use a clear structure, maintain a neutral tone, and include citations to sources. "
                "Do not think step by step. /no_think"
            ),
            user_prompt="\n".join(
                [
                    f"Query: {state.request.query}",
                    "",
                    "Research notes:",
                    state.research_notes or "No research notes were available.",
                    "",
                    "Analysis notes:",
                    state.analysis_notes or "No analysis notes were available.",
                    "",
                    "Sources:",
                    source_section,
                    "",
                    "Draft a comprehensive response based on the above information. "
                    "If applicable, mention how the findings can be applied in a production environment.",
                    "Return only the final answer. /no_think",
                ]
            ),
        )
        state.final_answer = response.content
        state.agent_results.append(
            AgentResult(
                agent=AgentName.WRITER,
                content=state.final_answer,
                metadata={
                    "citation_count": len(citations),
                    "input_tokens": response.input_tokens,
                    "output_tokens": response.output_tokens,
                    "cost_usd": response.cost_usd,
                    "llm": response.metadata,
                },
            )
        )
        state.add_trace_event("writer.complete", {"citation_count": len(citations)})
        return state
