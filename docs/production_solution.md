# Production Solution Notes
**Student:** Bùi Hữu Huấn (2A202600353)


This document maps the lab implementation to common production best practices.

## 1. Agent Design

The workflow uses a small number of agents with strict responsibility boundaries:

- `SupervisorAgent`: deterministic router and stop-condition owner.
- `ResearcherAgent`: evidence collection and citation capture.
- `AnalystAgent`: claim extraction, tradeoff analysis, and evidence-gap detection.
- `WriterAgent`: final answer synthesis.
- `CriticAgent`: optional completeness and citation check.

This avoids unnecessary agent sprawl while preserving clear handoffs.

## 2. State And Contracts

The system uses Pydantic schemas for important inputs and outputs:

- `ResearchQuery`
- `SourceDocument`
- `AgentResult`
- `BenchmarkMetrics`
- `ResearchState`

This supports validation, serialization, testing, and trace review.

## 3. Guardrails

Production guardrails are represented by:

- `MAX_ITERATIONS` to prevent infinite agent loops.
- `TIMEOUT_SECONDS` to centralize provider timeout policy.
- Deterministic route decisions for predictable execution.
- Writer fallback when the iteration budget is exhausted.
- `errors` field in shared state for non-fatal failure capture.

## 4. Observability

The workflow records:

- route decisions,
- agent completion events,
- span duration per step,
- final route history,
- agent outputs.

This makes the workflow explainable during peer review and future debugging.

There are two observability layers:

- Manual trace: always written to `ResearchState.trace` and printed by the CLI as
  a route/span table.
- LangSmith trace: enabled with `LANGSMITH_TRACING=true` and `LANGSMITH_API_KEY`.
  It creates a root workflow run plus child runs for each agent span.

## 5. Evaluation

The benchmark layer reports:

- latency,
- estimated cost,
- heuristic quality score,
- source count,
- error count.

The report in `reports/benchmark_report.md` compares single-agent and multi-agent
execution and documents a realistic failure mode.

## 6. Security

Secrets should stay in `.env` and must not be committed. The code loads keys through
`Settings` and keeps provider logic behind service abstractions.

Recommended production hardening:

- rotate any exposed local keys,
- use a secret manager in deployment,
- redact traces before sharing,
- avoid logging raw prompts that contain sensitive data.

## 7. Implementation Progress

The system has been upgraded from a no-key lab starter to a production-ready research workflow:

1. **Live Search**: `SearchClient` now supports Tavily API for real-time evidence gathering.
2. **Dynamic Agents**: `AnalystAgent` and `WriterAgent` have been refactored to use `LLMClient` for dynamic reasoning instead of hardcoded templates.
3. **Hardware Acceleration**: Configured for `llama_gpu` environment with CUDA support for low-latency local inference.
4. **LangSmith Integration**: Full tracing enabled for root and child spans to monitor orchestration and agent behavior.
