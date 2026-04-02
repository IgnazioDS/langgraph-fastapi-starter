# EXTENSION POINT: Add your agent's steps here as node functions.
# A node function takes AgentState and returns a dict of state updates.
# Register your node in graph.py with graph_builder.add_node("name", function).
#
# Example:
# def validate_input(state: AgentState) -> dict:
#     """Validate user input before passing to the model."""
#     ...

import logging
from typing import Literal

from langchain_core.messages import SystemMessage
from langchain_openai import ChatOpenAI

from app.config import config
from app.graph.state import AgentState
from app.graph.tools import TOOLS, retrieve_documents

logger = logging.getLogger(__name__)


def retrieve_context(state: AgentState) -> dict:
    """Retrieve relevant document chunks based on the latest user message.

    Runs before the model call so retrieved context can be injected as a system message.
    Calls retrieve_documents directly (not via LLM tool call).
    """
    messages = state["messages"]
    if not messages:
        return {"context": []}

    # Use the last user message as the retrieval query
    last_message = messages[-1]
    query = str(last_message.content) if last_message.content else ""

    if not query.strip():
        return {"context": []}

    result = retrieve_documents.invoke({"query": query, "top_k": 5})
    logger.debug(
        "context_retrieved",
        extra={
            "session_id": state.get("session_id", ""),
            "query": query[:100],
            "result_length": len(result),
        },
    )

    # If retrieval returned a real result (not the "no documents" message), store it
    no_docs_msg = "No documents are indexed"
    if no_docs_msg in result:
        return {"context": []}

    return {"context": [result]}


def call_model(state: AgentState) -> dict:
    """Invoke the LLM with the current message history and any retrieved context.

    Binds all tools to the model so it can emit tool calls.
    Tracks token usage for the response.
    """
    llm = ChatOpenAI(
        model=config.llm_model,
        api_key=config.openai_api_key,  # type: ignore[arg-type]
    ).bind_tools(TOOLS)

    messages = list(state["messages"])

    # Prepend retrieved context as a system message if available
    context = state.get("context", [])
    if context:
        context_text = "\n\n".join(context)
        system_msg = SystemMessage(
            content=(
                "Use the following retrieved context to help answer the user's question:\n\n"
                f"{context_text}"
            )
        )
        messages = [system_msg, *messages]

    response = llm.invoke(messages)

    # Extract token usage from response metadata
    usage_metadata = getattr(response, "usage_metadata", None) or {}
    input_tokens = int(usage_metadata.get("input_tokens", 0))
    output_tokens = int(usage_metadata.get("output_tokens", 0))

    return {
        "messages": [response],
        "input_tokens": state.get("input_tokens", 0) + input_tokens,
        "output_tokens": state.get("output_tokens", 0) + output_tokens,
    }


def should_continue(state: AgentState) -> Literal["tools", "end"]:
    """Routing function: continue to tools if the model emitted a tool call, else end."""
    messages = state["messages"]
    if not messages:
        return "end"

    last_message = messages[-1]
    tool_calls = getattr(last_message, "tool_calls", None)
    if tool_calls:
        return "tools"
    return "end"
