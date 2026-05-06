"""Tracing hooks for manual logs and optional LangSmith traces."""

import logging
import os
from collections.abc import Iterator
from contextlib import contextmanager
from time import perf_counter
from typing import Any

from multi_agent_research_lab.core.config import Settings, get_settings

logger = logging.getLogger(__name__)


@contextmanager
def langsmith_workflow_trace(
    name: str,
    inputs: dict[str, Any],
    settings: Settings | None = None,
) -> Iterator[Any | None]:
    """Create a root LangSmith run when explicitly enabled."""

    settings = settings or get_settings()
    if not settings.langsmith_tracing or not settings.langsmith_api_key:
        yield None
        return

    try:
        from langsmith import Client
        from langsmith.run_helpers import trace

        # LangSmith also reads these env vars internally. Set them here so traces
        # do not fall back to a random/default project when the CLI is launched
        # from a shell that already has LangSmith-related environment variables.
        os.environ["LANGSMITH_TRACING"] = "true"
        os.environ["LANGCHAIN_TRACING_V2"] = "true"
        os.environ["LANGSMITH_PROJECT"] = settings.langsmith_project
        os.environ["LANGCHAIN_PROJECT"] = settings.langsmith_project
        os.environ["LANGSMITH_API_KEY"] = settings.langsmith_api_key
        if settings.langsmith_endpoint:
            os.environ["LANGSMITH_ENDPOINT"] = settings.langsmith_endpoint

        client = Client(
            api_key=settings.langsmith_api_key,
            api_url=settings.langsmith_endpoint,
        )
        client.create_project(
            settings.langsmith_project,
            description="Multi-agent research lab traces",
            metadata={"app_env": settings.app_env, "source": "multi_agent_research_lab"},
            upsert=True,
        )
        logger.info("LangSmith project ready: %s", settings.langsmith_project)
        with trace(
            name,
            run_type="chain",
            inputs=inputs,
            project_name=settings.langsmith_project,
            client=client,
            tags=["multi-agent", "production-lab"],
            metadata={"app_env": settings.app_env},
        ) as root_run:
            logger.info("LangSmith root trace started: %s", root_run.get_url())
            yield root_run
    except Exception as exc:
        logger.warning("LangSmith tracing disabled after setup failure: %s", exc)
        yield None


@contextmanager
def trace_span(
    name: str,
    attributes: dict[str, Any] | None = None,
    parent: Any | None = None,
) -> Iterator[dict[str, Any]]:
    """Record a manual span and optionally mirror it to LangSmith."""

    started = perf_counter()
    span: dict[str, Any] = {
        "name": name,
        "attributes": attributes or {},
        "duration_seconds": None,
        "langsmith_url": None,
    }
    child_run = None
    if parent is not None:
        try:
            child_run = parent.create_child(
                name=name,
                run_type="chain",
                inputs={"attributes": span["attributes"]},
            )
            child_run.post()
        except Exception as exc:
            logger.warning("Failed to create LangSmith child span %s: %s", name, exc)
            child_run = None

    logger.info("agent.span.start name=%s attributes=%s", name, span["attributes"])
    error: str | None = None
    try:
        yield span
    except Exception as exc:
        error = repr(exc)
        raise
    finally:
        span["duration_seconds"] = perf_counter() - started
        if child_run is not None:
            try:
                child_run.end(outputs={"span": span}, error=error)
                child_run.patch()
                span["langsmith_url"] = child_run.get_url()
            except Exception as exc:
                logger.warning("Failed to finish LangSmith child span %s: %s", name, exc)
        logger.info(
            "agent.span.end name=%s duration_seconds=%.4f error=%s",
            name,
            span["duration_seconds"],
            error,
        )
