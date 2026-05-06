# Lab 20: Multi-Agent Research System

This project is a **production-oriented multi-agent research assistant**. It
compares a single-agent baseline with a multi-agent workflow:

```text
Supervisor -> Researcher -> Analyst -> Writer -> done
```

The current implementation is designed to run in `conda activate llama_gpu`
without API keys. It uses offline/local fallbacks so the lab can be tested on a
machine with limited GPU memory or no network access.

By default the project loads a local GGUF model with `llama-cpp-python`:

```text
WEIGHT/Qwen_Qwen3.5-0.8B-Q4_K_M.gguf
```

If the GGUF file or `llama-cpp-python` is unavailable, `LLMClient` falls back to a
deterministic local heuristic response so tests and CLI commands still complete.

Each LLM call prints which model path/provider is being used through the standard
logger. Example:

```text
INFO multi_agent_research_lab.services.llm_client - llm.model provider=local_gguf path=...Qwen_Qwen3.5-0.8B-Q4_K_M.gguf n_ctx=2048 n_gpu_layers=-1 max_tokens=512
INFO multi_agent_research_lab.services.llm_client - llm.model provider=local_gguf status=ok model=Qwen_Qwen3.5-0.8B-Q4_K_M.gguf input_tokens=371 output_tokens=334
```

## Production Solution Highlights

This repo intentionally includes the best-practice keywords and implementation
patterns expected in a production solution:

- **Clear agent roles**: Supervisor routes; Researcher gathers evidence; Analyst
  extracts claims and tradeoffs; Writer synthesizes the final answer.
- **Shared state**: Pydantic models keep request, sources, route history, notes,
  final answer, traces, and errors in one auditable state object.
- **Guardrails**: `MAX_ITERATIONS`, `TIMEOUT_SECONDS`, deterministic routing,
  fallback behavior, and validation-friendly schemas.
- **Observability**: each route and agent span is recorded in `state.trace`.
- **Evaluation**: benchmark helpers measure latency, cost estimate, quality score,
  source count, and error count.
- **Security**: API keys are loaded from `.env`; no secrets are hard-coded in code.
- **Offline fallback**: local search corpus and deterministic LLM response allow
  repeatable tests without OpenAI/Tavily/LangSmith keys.
- **Extensibility**: provider-specific LLM/search/tracing logic lives behind
  service abstractions instead of being embedded inside agents.

## Architecture

```text
User Query
   |
   v
ResearchState
   |
   v
Supervisor / Router
   |------> Researcher Agent  -> sources + research_notes
   |------> Analyst Agent     -> analysis_notes
   |------> Writer Agent      -> final_answer
   |
   v
Trace + Benchmark Report
```

## Repository Structure

```text
.
|-- src/multi_agent_research_lab/
|   |-- agents/              # Agent interfaces and role implementations
|   |-- core/                # Config, state, schemas, and domain errors
|   |-- graph/               # Workflow orchestration
|   |-- services/            # LLM, search, and storage abstractions
|   |-- evaluation/          # Benchmark and report helpers
|   |-- observability/       # Logging and trace spans
|   `-- cli.py               # CLI entrypoint
|-- configs/                 # YAML configs for lab variants
|-- docs/                    # Lab guide, rubric, design notes
|-- reports/                 # Benchmark deliverables
|-- tests/                   # Unit tests
`-- pyproject.toml           # Python project config
```

## Quickstart With `llama_gpu`

```powershell
conda activate llama_gpu
$env:PYTHONPATH="src"
python -m pytest -p no:cacheprovider
python -m ruff check src tests --no-cache
```

Check the local model directly:

```powershell
python -c "from multi_agent_research_lab.services.llm_client import LLMClient; r=LLMClient().complete('You are concise.', 'Say LOCAL_MODEL_OK in one short sentence. /no_think'); print(r.content); print(r.metadata)"
```

Run the baseline:

```powershell
$env:PYTHONPATH="src"
python -m multi_agent_research_lab.cli baseline `
  --query "Research GraphRAG state-of-the-art and write a 500-word summary"
```

Run the multi-agent workflow:

```powershell
$env:PYTHONPATH="src"
python -m multi_agent_research_lab.cli multi-agent `
  --query "Research GraphRAG state-of-the-art and write a 500-word summary"
```

Expected route:

```text
researcher -> analyst -> writer -> done
```

The CLI prints a **Manual Agent Trace** table before the JSON state. This is the
hand-written log path for explaining how the agents moved through the workflow:

```text
Step | Event | Agent / Route | Duration (s) | LangSmith
1    | route | researcher    |              |
     | span  | researcher    | 0.0012       |
2    | route | analyst       |              |
     | span  | analyst       | 0.0004       |
3    | route | writer        |              |
     | span  | writer        | 8.4123       |
4    | route | done          |              |
```

Hide the table if you only want JSON:

```powershell
python -m multi_agent_research_lab.cli multi-agent `
  --query "Research GraphRAG state-of-the-art and write a 500-word summary" `
  --hide-trace
```

## LangSmith Tracing

Manual trace is always available. LangSmith tracing is optional and must be enabled
explicitly so tests and offline demos do not accidentally call the network.

Check current tracing configuration without printing secrets:

```powershell
python -m multi_agent_research_lab.cli trace-status
```

Verify the LangSmith API key and create the configured project if it does not
exist yet:

```powershell
python -m multi_agent_research_lab.cli langsmith-check
```

Add these values to `.env`:

```env
LANGSMITH_API_KEY=your_langsmith_key
LANGSMITH_TRACING=true
LANGSMITH_ENDPOINT=https://api.smith.langchain.com
LANGSMITH_PROJECT=multi-agent-research-lab
```

When enabled, the workflow creates:

- one root run named `multi-agent-research-workflow`;
- child runs for `supervisor`, `researcher`, `analyst`, and `writer`;
- outputs containing `route_history`, `final_answer_preview`, and `errors`;
- LangSmith URLs inside `state.trace` and the CLI trace table when available.

Production notes:

- keep `LANGSMITH_TRACING=false` for unit tests and private/offline demos;
- redact sensitive prompts before sharing traces;
- use `LANGSMITH_PROJECT` to separate experiments, staging, and production runs;
- manual trace remains the fallback if LangSmith setup or network calls fail.

How to view the trace:

1. Run `python -m multi_agent_research_lab.cli trace-status` and confirm
   `LangSmith API key = set` and `LangSmith tracing = enabled`.
2. Run the multi-agent command.
3. Look at the `LangSmith` column in the manual trace table or the
   `langsmith.root` event in JSON output.
4. Open the printed URL, or go to `https://smith.langchain.com/` and choose the
   `multi-agent-research-lab` project.

If the LangSmith column is empty and JSON shows `"langsmith_url": null`, the run
was local/manual only. The most common cause is missing `LANGSMITH_TRACING=true`
in `.env`. If logs show `Project ... not found`, run `langsmith-check` once or
open LangSmith and create a project named `multi-agent-research-lab`.

## Best-Practice Checklist

| Area | Production practice | Implemented in |
|---|---|---|
| Role design | Single responsibility per agent | `src/multi_agent_research_lab/agents/` |
| State management | Typed shared state and schemas | `core/state.py`, `core/schemas.py` |
| Routing | Deterministic, bounded policy | `agents/supervisor.py` |
| Guardrails | Max iterations, timeout config, fallback | `core/config.py`, `graph/workflow.py` |
| Observability | Trace spans and route events | `observability/tracing.py` |
| LangSmith tracing | Optional root and child runs | `observability/tracing.py`, `.env.example` |
| Evaluation | Baseline vs multi-agent metrics | `evaluation/benchmark.py` |
| Security | Environment-based secrets | `.env.example`, `core/config.py` |
| Reliability | Offline fallback for no-key execution | `services/search_client.py`, `services/llm_client.py` |
| Local inference | GGUF model loading through llama.cpp | `services/llm_client.py`, `WEIGHT/` |

Local model defaults:

```text
LOCAL_MODEL_PATH=WEIGHT/Qwen_Qwen3.5-0.8B-Q4_K_M.gguf
LOCAL_MODEL_N_CTX=2048
LOCAL_MODEL_N_GPU_LAYERS=-1
LOCAL_MODEL_MAX_TOKENS=512
```

## Deliverables

1. Working repository with tests passing.
2. Trace output showing which agent ran and why.
3. `reports/benchmark_report.md` comparing single-agent and multi-agent runs.
4. Failure mode analysis with mitigation plan.

## Useful Commands

```powershell
conda activate llama_gpu
$env:PYTHONPATH="src"
python -m pytest -p no:cacheprovider
python -m ruff check src tests --no-cache
rg -n "TODO\(student\)" src tests docs
```

## References

- Anthropic: Building effective agents - https://www.anthropic.com/engineering/building-effective-agents
- OpenAI Agents SDK orchestration/handoffs - https://developers.openai.com/api/docs/guides/agents/orchestration
- LangGraph concepts - https://langchain-ai.github.io/langgraph/concepts/
- LangSmith tracing - https://docs.smith.langchain.com/
- Langfuse tracing - https://langfuse.com/docs
