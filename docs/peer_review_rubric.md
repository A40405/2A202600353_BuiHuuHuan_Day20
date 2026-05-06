# Peer Review Rubric

Use this rubric to review whether the repo looks like a **best-practice,
production-ready multi-agent solution**, not only a demo that prints a good answer.

## Scoring

| Criterion | Production question | Score |
|---|---|---:|
| Role clarity | Does each agent have one clear responsibility with low overlap? | 0-2 |
| State design | Is shared state typed, auditable, and sufficient for handoff/debugging? | 0-2 |
| Guardrails | Are max iterations, timeout config, fallback, and validation present? | 0-2 |
| Observability | Can reviewers explain manual logs, LangSmith spans, errors, and outputs? | 0-2 |
| Benchmark | Does it compare baseline vs multi-agent with concrete metrics? | 0-2 |

## Best-Practice Keywords To Look For

- **single responsibility**
- **shared state**
- **typed schema**
- **deterministic routing**
- **guardrails**
- **max iterations**
- **timeout**
- **retry/fallback**
- **validation**
- **observability**
- **trace**
- **manual trace**
- **LangSmith**
- **root run**
- **child span**
- **benchmark**
- **latency**
- **cost**
- **quality score**
- **citation coverage**
- **failure mode**
- **security**
- **no hard-coded secrets**
- **provider abstraction**
- **offline fallback**

## Feedback Format

```text
Strength:
Risk / failure mode:
Production best-practice gap:
One concrete improvement:
Score:
```

## Example Review

```text
Strength: Clear Supervisor -> Researcher -> Analyst -> Writer route with trace events.
Risk / failure mode: Offline search corpus can become stale for fast-moving topics.
Production best-practice gap: Live retrieval and stronger citation validation are not yet integrated.
One concrete improvement: Add Tavily/Bing implementation behind SearchClient while preserving the local fallback.
Score: 8/10
```
