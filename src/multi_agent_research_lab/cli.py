"""Command-line entrypoint for the lab starter."""

from typing import Annotated

import typer
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from multi_agent_research_lab.core.config import get_settings
from multi_agent_research_lab.core.schemas import ResearchQuery
from multi_agent_research_lab.core.state import ResearchState
from multi_agent_research_lab.graph.workflow import MultiAgentWorkflow
from multi_agent_research_lab.observability.logging import configure_logging
from multi_agent_research_lab.services.llm_client import LLMClient
from multi_agent_research_lab.services.search_client import SearchClient

app = typer.Typer(help="Multi-Agent Research Lab starter CLI")
console = Console()


def _init() -> None:
    settings = get_settings()
    configure_logging(settings.log_level)


@app.command()
def baseline(
    query: Annotated[str, typer.Option("--query", "-q", help="Research query")],
) -> None:
    """Run a minimal single-agent baseline."""

    _init()
    request = ResearchQuery(query=query)
    state = ResearchState(request=request)
    sources = SearchClient().search(query, request.max_sources)
    source_notes = "\n".join(f"- {source.title}: {source.snippet}" for source in sources)
    response = LLMClient().complete(
        system_prompt=(
            "You are a concise single-agent research assistant. "
            "Do not think step by step."
        ),
        user_prompt=(
            f"Question: {query}\n\n"
            f"Sources:\n{source_notes}\n\n"
            "Return only the final answer. /no_think"
        ),
    )
    state.sources = sources
    state.final_answer = response.content
    console.print(Panel.fit(state.final_answer, title="Single-Agent Baseline"))


@app.command("multi-agent")
def multi_agent(
    query: Annotated[str, typer.Option("--query", "-q", help="Research query")],
    show_trace: Annotated[
        bool,
        typer.Option("--show-trace/--hide-trace", help="Print manual agent route trace"),
    ] = True,
) -> None:
    """Run the multi-agent workflow."""

    _init()
    state = ResearchState(request=ResearchQuery(query=query))
    workflow = MultiAgentWorkflow()
    result = workflow.run(state)
    if show_trace:
        _print_manual_trace(result)
    console.print(result.model_dump_json(indent=2))


@app.command("trace-status")
def trace_status() -> None:
    """Show local and LangSmith tracing status without printing secrets."""

    _init()
    settings = get_settings()
    table = Table(title="Tracing Status")
    table.add_column("Item")
    table.add_column("Value")
    table.add_row("Manual trace", "enabled")
    table.add_row("LangSmith API key", "set" if settings.langsmith_api_key else "missing")
    table.add_row("LangSmith tracing", "enabled" if settings.langsmith_tracing else "disabled")
    table.add_row("LangSmith endpoint", settings.langsmith_endpoint or "default")
    table.add_row("LangSmith project", settings.langsmith_project)
    table.add_row("Local LLM", "enabled" if settings.local_llm_enabled else "disabled")
    table.add_row("Local model", settings.local_model_path)
    console.print(table)
    if settings.langsmith_api_key and not settings.langsmith_tracing:
        console.print(
            Panel.fit(
                "LANGSMITH_API_KEY is set, but LANGSMITH_TRACING is false or missing. "
                "Set LANGSMITH_TRACING=true in .env to send traces.",
                title="LangSmith Not Sending",
                style="yellow",
            )
        )


@app.command("langsmith-check")
def langsmith_check() -> None:
    """Verify LangSmith connectivity and create the configured project if needed."""

    _init()
    settings = get_settings()
    if not settings.langsmith_api_key:
        console.print(Panel.fit("LANGSMITH_API_KEY is missing.", title="LangSmith", style="red"))
        raise typer.Exit(code=2)
    try:
        from langsmith import Client

        client = Client(
            api_key=settings.langsmith_api_key,
            api_url=settings.langsmith_endpoint,
        )
        project = client.create_project(
            settings.langsmith_project,
            description="Multi-agent research lab traces",
            metadata={"app_env": settings.app_env, "source": "multi_agent_research_lab"},
            upsert=True,
        )
    except Exception as exc:
        console.print(Panel.fit(str(exc), title="LangSmith Check Failed", style="red"))
        raise typer.Exit(code=2) from exc

    console.print(
        Panel.fit(
            f"LangSmith connection OK.\nProject: {project.name}",
            title="LangSmith Check",
            style="green",
        )
    )


def _print_manual_trace(state: ResearchState) -> None:
    table = Table(title="Manual Agent Trace")
    table.add_column("Step", justify="right")
    table.add_column("Event")
    table.add_column("Agent / Route")
    table.add_column("Duration (s)", justify="right")
    table.add_column("LangSmith")

    step = 0
    for event in state.trace:
        name = event["name"]
        payload = event["payload"]
        if name == "supervisor.route":
            step += 1
            table.add_row(
                str(step),
                "route",
                str(payload.get("route", "")),
                "",
                "",
            )
        elif name.startswith("span."):
            table.add_row(
                "",
                "span",
                str(payload.get("name", name.replace("span.", ""))),
                _format_duration(payload.get("duration_seconds")),
                str(payload.get("langsmith_url") or ""),
            )
        elif name == "langsmith.root":
            table.add_row("", "root", "workflow", "", str(payload.get("url", "")))
    console.print(table)


def _format_duration(value: object) -> str:
    if isinstance(value, int | float):
        return f"{value:.4f}"
    return ""


if __name__ == "__main__":
    app()
