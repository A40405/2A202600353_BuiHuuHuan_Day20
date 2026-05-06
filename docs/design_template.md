# Design Template
**Student:** Bùi Hữu Huấn (2A202600353)


## Problem

Build a research assistant that receives an open-ended query, gathers source-shaped
evidence, analyzes tradeoffs, and writes a final answer with traceable citations.

Example query:

```text
Research GraphRAG state-of-the-art and write a 500-word summary
```

## Why multi-agent?

A single agent is enough for short factual tasks, but this lab query benefits from
separating evidence collection, analysis, and writing. The split makes handoff state
visible, gives each step a smaller responsibility, and makes failures easier to debug.

## Agent roles

| Agent | Responsibility | Input | Output | Failure mode |
|---|---|---|---|---|
| Supervisor | Route the workflow and stop when complete | Shared state | Next route | Bad route or loop |
| Researcher | Collect local/mock source documents and notes | Query, max sources | Sources, research notes | Weak or missing evidence |
| Analyst | Extract claims, tradeoffs, and gaps | Research notes | Analysis notes | Runs before evidence exists |
| Writer | Synthesize final answer and citations | Sources, analysis notes | Final answer | Missing citations or shallow synthesis |
| Critic | Optional completeness and citation check | Final answer, sources | Critic findings | Overly simple validation |

## Shared state

| Field | Reason |
|---|---|
| `request` | Stores the original query, audience, and source limit |
| `iteration` | Enforces bounded execution |
| `route_history` | Explains the workflow path |
| `sources` | Preserves evidence for citations |
| `research_notes` | Handoff from Researcher to Analyst |
| `analysis_notes` | Handoff from Analyst to Writer |
| `final_answer` | Final user-facing output |
| `agent_results` | Structured record of each agent output |
| `trace` | Debug timing and route events |
| `errors` | Non-fatal failures and validation issues |

## Routing policy

```text
start
  -> supervisor
  -> researcher if research_notes is missing
  -> analyst if analysis_notes is missing
  -> writer if final_answer is missing
  -> done when final_answer exists
```

The Supervisor also checks `MAX_ITERATIONS`. If the limit is reached before a final
answer exists, the workflow falls back to Writer with the best available state.

## Guardrails

- Max iterations: `MAX_ITERATIONS`, default 6.
- Timeout: `TIMEOUT_SECONDS`, default 60, ready for provider calls.
- Retry: keep provider retries inside `LLMClient` or future `SearchClient`.
- Fallback: offline local corpus and deterministic local LLM response.
- Validation: Pydantic schemas plus optional Critic checks.

## Benchmark plan

| Query | Metric | Expected outcome |
|---|---|---|
| GraphRAG state-of-the-art summary | Latency, quality, citation coverage | Multi-agent gives clearer structure |
| Single vs multi-agent support workflow | Latency, quality | Baseline is faster, multi-agent is more auditable |
| Production guardrails for LLM agents | Failure rate, coverage | Multi-agent trace exposes missing guardrails |
