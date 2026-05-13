# EXTENSION POINT: Add nodes and edges to modify the graph structure.
# To add a node: builder.add_node("your_node_name", your_node_function)
# To add an edge: builder.add_edge("from_node", "to_node")
# To add conditional routing: builder.add_conditional_edges(...)
#
# To swap the entire graph: implement your own build_graph() function
# and call it in init_graph(). The rest of the app uses get_graph()
# and does not care what the graph contains.

from langgraph.graph import END, StateGraph
from langgraph.graph.state import CompiledStateGraph
from langgraph.prebuilt import ToolNode

from app.graph.nodes import call_model, retrieve_context, should_continue
from app.graph.state import AgentState
from app.graph.tools import TOOLS


def build_graph() -> CompiledStateGraph[AgentState, None, AgentState, AgentState]:
    """Build and compile the agent graph.

    Graph flow:
      retrieve (fetch context) → agent (LLM call) → [tools? → agent] → END
    """
    builder: StateGraph[AgentState, None, AgentState, AgentState] = StateGraph(AgentState)

    builder.add_node("retrieve", retrieve_context)
    builder.add_node("agent", call_model)
    builder.add_node("tools", ToolNode(TOOLS))

    builder.set_entry_point("retrieve")
    builder.add_edge("retrieve", "agent")
    builder.add_conditional_edges(
        "agent",
        should_continue,
        {"tools": "tools", "end": END},
    )
    builder.add_edge("tools", "agent")

    return builder.compile()


# Module-level compiled graph — initialized once at startup via init_graph().
_graph: CompiledStateGraph[AgentState, None, AgentState, AgentState] | None = None


def get_graph() -> CompiledStateGraph[AgentState, None, AgentState, AgentState]:
    """Return the compiled graph. Raises if init_graph() has not been called."""
    if _graph is None:
        raise RuntimeError("Graph not initialized. Call init_graph() at startup.")
    return _graph


def init_graph() -> None:
    """Compile and store the graph. Called once during application startup."""
    global _graph
    _graph = build_graph()
