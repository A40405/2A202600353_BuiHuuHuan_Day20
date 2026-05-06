"""Workflow orchestration for the lab."""

from collections.abc import Callable

from multi_agent_research_lab.agents import (
    AnalystAgent,
    ResearcherAgent,
    SupervisorAgent,
    WriterAgent,
)
from multi_agent_research_lab.core.config import get_settings
from multi_agent_research_lab.core.errors import AgentExecutionError
from multi_agent_research_lab.core.state import ResearchState
from multi_agent_research_lab.observability.tracing import langsmith_workflow_trace, trace_span


class MultiAgentWorkflow:
    """Builds and runs the multi-agent graph.

    Keep orchestration here; keep agent internals in `agents/`.
    """

    def build(self) -> object:
        """Create the executable workflow map.

        A dict keeps the no-API lab path dependency-light while preserving the
        same node names that a LangGraph implementation would use.
        """

        return {
            "supervisor": SupervisorAgent(),
            "researcher": ResearcherAgent(),
            "analyst": AnalystAgent(),
            "writer": WriterAgent(),
        }

    def run(self, state: ResearchState) -> ResearchState:
        """Execute the graph and return final state."""

        settings = get_settings()
        graph = self.build()
        supervisor = graph["supervisor"]
        workers: dict[str, Callable[[ResearchState], ResearchState]] = {
            "researcher": graph["researcher"].run,
            "analyst": graph["analyst"].run,
            "writer": graph["writer"].run,
        }

        with langsmith_workflow_trace(
            "multi-agent-research-workflow",
            inputs={"query": state.request.query, "audience": state.request.audience},
            settings=settings,
        ) as root_run:
            while state.iteration < settings.max_iterations:
                with trace_span(
                    "supervisor",
                    {"iteration": state.iteration + 1},
                    parent=root_run,
                ) as span:
                    state = supervisor.run(state)
                state.add_trace_event("span.supervisor", span)

                route = state.route_history[-1]
                state.add_trace_event(
                    "manual.route",
                    {"step": state.iteration, "next_agent": route},
                )
                if route == "done":
                    _finish_root_trace(root_run, state)
                    return state
                if route not in workers:
                    raise AgentExecutionError(f"Unknown supervisor route: {route}")

                with trace_span(
                    route,
                    {"iteration": state.iteration, "query": state.request.query},
                    parent=root_run,
                ) as span:
                    state = workers[route](state)
                state.add_trace_event(f"span.{route}", span)

            if state.final_answer is None:
                state = workers["writer"](state)
            state.add_trace_event("workflow.max_iterations", {"limit": settings.max_iterations})
            _finish_root_trace(root_run, state)
        return state


def _finish_root_trace(root_run: object | None, state: ResearchState) -> None:
    if root_run is None:
        return
    try:
        root_run.add_outputs(
            {
                "route_history": state.route_history,
                "final_answer_preview": (state.final_answer or "")[:500],
                "errors": state.errors,
            }
        )
        state.add_trace_event("langsmith.root", {"url": root_run.get_url()})
    except Exception as exc:
        state.add_trace_event("langsmith.error", {"error": repr(exc)})
