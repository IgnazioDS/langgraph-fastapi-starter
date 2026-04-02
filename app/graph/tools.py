# EXTENSION POINT: Add your custom tools here.
# Each tool is a function decorated with @tool.
# Add it to the TOOLS list at the bottom of this file.
# Then import it in graph.py and pass it to bind_tools().
#
# Example:
# @tool
# def query_your_database(query: str) -> str:
#     """Query your product database. Use when the user asks about..."""
#     ...

import logging

from langchain_core.tools import tool

from app.config import config

logger = logging.getLogger(__name__)


@tool
def web_search(query: str) -> str:
    """Search the web for current information. Use when the user asks about recent events,
    facts you may not know, or anything that requires up-to-date information."""
    if not config.tavily_api_key:
        return (
            "Web search is not configured. Set TAVILY_API_KEY to enable it."
        )

    try:
        from tavily import TavilyClient  # type: ignore[import-untyped]

        client = TavilyClient(api_key=config.tavily_api_key)
        results = client.search(query=query, max_results=3)
        formatted: list[str] = []
        for r in results.get("results", []):
            title = r.get("title", "No title")
            url = r.get("url", "")
            snippet = r.get("content", "No content")
            formatted.append(f"**{title}**\n{url}\n{snippet}")
        return "\n\n".join(formatted) if formatted else "No results found."
    except Exception as e:
        logger.warning("web_search_failed", extra={"query": query, "error": str(e)})
        return f"Web search failed: {e}"


@tool
def retrieve_documents(query: str, top_k: int = 5) -> str:
    """Retrieve relevant documents from the knowledge base. Use when the user asks about
    topics that may be covered in indexed documents."""
    try:
        from openai import OpenAI

        from app.db.connection import db_conn

        openai_client = OpenAI(api_key=config.openai_api_key)
        embed_response = openai_client.embeddings.create(
            input=query,
            model=config.embedding_model,
        )
        embedding = embed_response.data[0].embedding

        with db_conn() as conn:
            with conn.cursor() as cur:
                # Check if documents table exists
                cur.execute(
                    """
                    SELECT EXISTS (
                        SELECT FROM information_schema.tables
                        WHERE table_name = 'documents'
                    )
                    """
                )
                row = cur.fetchone()
                if row is None or not row[0]:
                    return "No documents are indexed. Add documents to enable retrieval."

                cur.execute(
                    """
                    SELECT content, source
                    FROM documents
                    ORDER BY embedding <=> %(embedding)s::vector
                    LIMIT %(top_k)s
                    """,
                    {"embedding": str(embedding), "top_k": top_k},
                )
                rows = cur.fetchall()

        if not rows:
            return "No documents are indexed. Add documents to enable retrieval."

        results = []
        for i, (content, source) in enumerate(rows, 1):
            results.append(f"{i}. [{source}]\n{content}")
        return "\n\n".join(results)

    except Exception as e:
        logger.warning("retrieve_documents_failed", extra={"query": query, "error": str(e)})
        return f"Document retrieval failed: {e}"


# All tools registered with the agent. Import this list in graph.py.
TOOLS: list = [web_search, retrieve_documents]
