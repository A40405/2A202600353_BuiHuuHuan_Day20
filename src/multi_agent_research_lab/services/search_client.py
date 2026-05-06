"""Search client abstraction for ResearcherAgent."""

import logging
from multi_agent_research_lab.core.config import get_settings
from multi_agent_research_lab.core.schemas import SourceDocument

logger = logging.getLogger(__name__)


class SearchClient:
    """Provider-agnostic search client with an offline corpus fallback.

    The lab can be completed without a search API key. This local corpus gives the
    Researcher realistic source-shaped data while keeping the integration point
    small enough to replace with Tavily, Bing, or an internal document index.
    """

    _LOCAL_CORPUS = [
        SourceDocument(
            title="Anthropic: Building effective agents",
            url="https://www.anthropic.com/engineering/building-effective-agents",
            snippet=(
                "Effective agent systems often start with simple workflows, clear tool "
                "boundaries, transparent orchestration, and escalation only when the task "
                "benefits from autonomy."
            ),
            metadata={"keywords": ["agent", "multi-agent", "workflow", "guardrails"]},
        ),
        SourceDocument(
            title="LangGraph concepts",
            url="https://langchain-ai.github.io/langgraph/concepts/",
            snippet=(
                "LangGraph models long-running agent applications as stateful graphs with "
                "nodes, edges, conditional routing, persistence, and human-in-the-loop hooks."
            ),
            metadata={"keywords": ["langgraph", "graph", "routing", "state"]},
        ),
        SourceDocument(
            title="GraphRAG: Retrieval-Augmented Generation over knowledge graphs",
            url="https://www.microsoft.com/en-us/research/project/graphrag/",
            snippet=(
                "GraphRAG combines graph extraction, community summaries, and retrieval to "
                "answer broad questions that require connecting evidence across documents."
            ),
            metadata={"keywords": ["graphrag", "rag", "knowledge graph", "retrieval"]},
        ),
        SourceDocument(
            title="Production guardrails for LLM applications",
            url=None,
            snippet=(
                "Common production guardrails include bounded iterations, timeouts, retries, "
                "fallbacks, structured validation, tracing, and regression evaluation."
            ),
            metadata={"keywords": ["guardrails", "timeout", "retry", "validation"]},
        ),
        SourceDocument(
            title="Single-agent vs multi-agent workflow tradeoffs",
            url=None,
            snippet=(
                "Single-agent systems are cheaper and easier to debug for narrow tasks. "
                "Multi-agent systems help when research, critique, and synthesis require "
                "distinct context windows or quality gates."
            ),
            metadata={"keywords": ["single-agent", "multi-agent", "benchmark"]},
        ),
    ]

    def search(self, query: str, max_results: int = 5) -> list[SourceDocument]:
        """Search for documents relevant to a query."""

        settings = get_settings()
        if settings.tavily_api_key:
            try:
                from tavily import TavilyClient

                client = TavilyClient(api_key=settings.tavily_api_key)
                logger.info("Performing live search with Tavily: %s", query)
                response = client.search(query=query, max_results=max_results)
                
                results = []
                for result in response.get("results", []):
                    results.append(
                        SourceDocument(
                            title=result.get("title", "Untitled"),
                            url=result.get("url"),
                            snippet=result.get("content", ""),
                            metadata={
                                "score": result.get("score"),
                                "raw": result
                            }
                        )
                    )
                return results
            except Exception as exc:
                logger.warning("Tavily search failed, falling back to local corpus: %s", exc)

        # Fallback to local corpus keyword matching
        query_terms = {term.strip(".,:;!?()[]").lower() for term in query.split()}

        def score(document: SourceDocument) -> int:
            keywords = {str(item).lower() for item in document.metadata.get("keywords", [])}
            haystack = f"{document.title} {document.snippet}".lower()
            keyword_hits = len(query_terms & keywords)
            text_hits = sum(1 for term in query_terms if len(term) > 3 and term in haystack)
            return keyword_hits * 3 + text_hits

        ranked = sorted(self._LOCAL_CORPUS, key=score, reverse=True)
        selected = [doc for doc in ranked if score(doc) > 0] or ranked
        return selected[:max_results]
