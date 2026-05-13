from langchain_core.messages import AIMessage, HumanMessage

from app.graph.nodes import should_continue
from app.graph.state import AgentState


def _make_state(**kwargs) -> AgentState:  # type: ignore[return]
    defaults: AgentState = {
        "messages": [],
        "session_id": "s1",
        "tenant_id": "t1",
        "context": [],
        "run_id": "r1",
        "input_tokens": 0,
        "output_tokens": 0,
    }
    defaults.update(kwargs)  # type: ignore[typeddict-item]
    return defaults


def test_should_continue_returns_tools_when_tool_calls_present() -> None:
    mock_tool_call = {
        "name": "web_search",
        "args": {"query": "test query"},
        "id": "call_abc123",
        "type": "tool_call",
    }
    msg = AIMessage(content="", tool_calls=[mock_tool_call])
    state = _make_state(messages=[msg])
    assert should_continue(state) == "tools"


def test_should_continue_returns_end_when_no_tool_calls() -> None:
    msg = AIMessage(content="Final answer here.")
    state = _make_state(messages=[msg])
    assert should_continue(state) == "end"


def test_should_continue_returns_end_for_empty_messages() -> None:
    state = _make_state(messages=[])
    assert should_continue(state) == "end"


def test_should_continue_returns_end_for_human_message() -> None:
    """Human messages never have tool_calls — should route to end."""
    msg = HumanMessage(content="What is 2+2?")
    state = _make_state(messages=[msg])
    assert should_continue(state) == "end"
