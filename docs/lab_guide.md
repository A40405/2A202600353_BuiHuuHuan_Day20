# Lab Guide: Multi-Agent Research System

## Scenario

Build a research assistant that receives a long-form question, gathers evidence,
analyzes it, and writes a final answer. The lab compares two approaches:

1. **Single-agent baseline**: one agent handles the full task.
2. **Multi-agent workflow**: Supervisor routes Researcher, Analyst, and Writer.

## Important Rules

- Do not add agents without a clear reason.
- Each agent must have a distinct responsibility.
- Shared state must be explicit enough for debugging.
- Each step must produce trace or log events.
- Benchmark the system instead of judging only by a pretty output.

## Milestone 1: Baseline

Relevant files:

- `src/multi_agent_research_lab/cli.py`
- `src/multi_agent_research_lab/services/llm_client.py`

Current implementation: the baseline uses a deterministic local LLM fallback and
offline source-shaped evidence, so it runs without an API key.

## Milestone 2: Supervisor

Relevant files:

- `src/multi_agent_research_lab/agents/supervisor.py`
- `src/multi_agent_research_lab/graph/workflow.py`

Current implementation: the Supervisor follows a deterministic route policy:

```text
researcher -> analyst -> writer -> done
```

It also respects the configured max-iteration guardrail.

For debugging, run the CLI with the default `--show-trace` option. It prints a
manual route/span table before the JSON state.

## Milestone 3: Worker Agents

Relevant files:

- `agents/researcher.py`
- `agents/analyst.py`
- `agents/writer.py`

Current implementation:

- Researcher searches the offline local corpus and writes source notes.
- Analyst extracts key claims, tradeoffs, and evidence gaps.
- Writer synthesizes the final answer with citations.

## Milestone 4: Trace And Benchmark

Relevant files:

- `observability/tracing.py`
- `evaluation/benchmark.py`
- `evaluation/report.py`
- `reports/benchmark_report.md`

Benchmark metrics:

| Metric | Measurement |
|---|---|
| Latency | Wall-clock time |
| Cost | Offline mode reports `$0.00` |
| Quality | Heuristic score plus peer review |
| Citation coverage | Number of captured sources and cited sources |
| Failure rate | Number of failed queries over total queries |

LangSmith tracing is optional. To enable provider tracing, set
`LANGSMITH_TRACING=true`, `LANGSMITH_API_KEY`, and `LANGSMITH_PROJECT` in `.env`.

## Exit Ticket

1. Use multi-agent workflows when the task benefits from distinct responsibilities,
   quality gates, or traceable handoffs.
2. Avoid multi-agent workflows for short, narrow tasks where one model call is faster,
   cheaper, and easier to debug.
