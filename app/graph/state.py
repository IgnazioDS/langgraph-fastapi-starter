from typing import Annotated, TypedDict

from langchain_core.messages import BaseMessage
from langgraph.graph.message import add_messages


class AgentState(TypedDict):
    # add_messages reducer appends new messages rather than replacing the list.
    # This is what enables the tool-call loop: each node adds to history.
    messages: Annotated[list[BaseMessage], add_messages]
    session_id: str
    tenant_id: str
    context: list[str]      # Retrieved document chunks injected as system context
    run_id: str
    input_tokens: int
    output_tokens: int
