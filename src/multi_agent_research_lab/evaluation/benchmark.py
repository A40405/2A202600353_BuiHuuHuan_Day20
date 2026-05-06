"""Benchmark helpers for single-agent vs multi-agent."""

from collections.abc import Callable
from time import perf_counter

from multi_agent_research_lab.core.schemas import BenchmarkMetrics
from multi_agent_research_lab.core.state import ResearchState

Runner = Callable[[str], ResearchState]


def run_benchmark(
    run_name: str,
    query: str,
    runner: Runner,
) -> tuple[ResearchState, BenchmarkMetrics]:
    """Measure latency and return basic no-API benchmark metrics."""

    started = perf_counter()
    state = runner(query)
    latency = perf_counter() - started
    citation_count = len(state.sources)
    has_answer = bool(state.final_answer)
    quality_score = 5.0
    if has_answer:
        quality_score += 1.0
    if state.research_notes:
        quality_score += 1.0
    if state.analysis_notes:
        quality_score += 1.0
    if citation_count:
        quality_score += 1.0
    if not state.errors:
        quality_score += 1.0

    metrics = BenchmarkMetrics(
        run_name=run_name,
        latency_seconds=latency,
        estimated_cost_usd=0.0,
        quality_score=min(quality_score, 10.0),
        notes=f"sources={citation_count}; errors={len(state.errors)}",
    )
    return state, metrics
