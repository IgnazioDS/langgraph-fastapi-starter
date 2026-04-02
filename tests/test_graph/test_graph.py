import pytest

from app.graph.graph import build_graph, get_graph, init_graph


def test_build_graph_compiles_without_error(_patch_config: None) -> None:
    """build_graph() should return a compiled graph without raising."""
    graph = build_graph()
    assert graph is not None


def test_get_graph_raises_before_init() -> None:
    """get_graph() must raise RuntimeError if called before init_graph()."""
    import app.graph.graph as graph_module

    original = graph_module._graph
    graph_module._graph = None
    try:
        with pytest.raises(RuntimeError, match="Graph not initialized"):
            get_graph()
    finally:
        graph_module._graph = original


def test_init_graph_sets_graph(_patch_config: None) -> None:
    import app.graph.graph as graph_module

    original = graph_module._graph
    graph_module._graph = None
    try:
        init_graph()
        graph = get_graph()
        assert graph is not None
    finally:
        graph_module._graph = original
