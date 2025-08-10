import pytest
from autobook_ai.main import app, AppState

def test_graph_execution():
    """
    Tests that the LangGraph application executes from end to end
    and produces a final state with the expected structure.
    """
    initial_state = {"user_request": "Test request"}
    final_state = app.invoke(initial_state)

    # Check that all expected keys are in the final state
    assert "user_request" in final_state
    assert "research_findings" in final_state
    assert "schedule" in final_state
    assert "confirmation" in final_state

    # Check that the values have the correct types
    assert isinstance(final_state["user_request"], str)
    assert isinstance(final_state["research_findings"], list)
    assert isinstance(final_state["schedule"], str)
    assert isinstance(final_state["confirmation"], str)

    # Check that the initial user request is preserved
    assert final_state["user_request"] == "Test request"
