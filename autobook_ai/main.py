import os
from langgraph.graph import StateGraph, END
from typing import TypedDict, Annotated
import operator

# 1. Define the state for our graph
class AppState(TypedDict):
    """
    The state of our application graph.
    It will be passed between nodes.
    """
    user_request: str
    research_findings: list[str]
    schedule: str
    confirmation: str

# 2. Define the agent nodes

def user_input_agent(state: AppState):
    """
    Parses the user input and updates the state.
    """
    print("---USER INPUT AGENT---")
    # For now, we'll just print the request.
    # In a real app, this would involve more sophisticated parsing.
    print(f"User request: {state['user_request']}")
    return {"user_request": state['user_request']}


def research_agent(state: AppState):
    """
    Performs research based on the user request.
    """
    print("---RESEARCH AGENT---")
    # This is a mock implementation.
    # In a real app, this would use RAG and other tools.
    findings = [
        "Dr. Smith is available at 2pm on Tuesday.",
        "The restaurant has a table for 2 at 7pm on Friday.",
        "The vet is open from 9am to 5pm on weekdays.",
    ]
    print(f"Research findings: {findings}")
    return {"research_findings": findings}


def scheduling_agent(state: AppState):
    """
    Creates a schedule based on the research findings.
    """
    print("---SCHEDULING AGENT---")
    # This is a mock implementation.
    schedule = "Booked appointment with Dr. Smith for 2pm on Tuesday."
    print(f"Proposed schedule: {schedule}")
    return {"schedule": schedule}


def confirmation_agent(state: AppState):
    """
    Confirms the schedule with the user.
    """
    print("---CONFIRMATION AGENT---")
    # This is a mock implementation.
    confirmation = "Your appointment with Dr. Smith is confirmed."
    print(f"Confirmation: {confirmation}")
    return {"confirmation": confirmation}


# 3. Wire up the nodes in a graph

workflow = StateGraph(AppState)

workflow.add_node("user_input", user_input_agent)
workflow.add_node("research", research_agent)
workflow.add_node("schedule", scheduling_agent)
workflow.add_node("confirm", confirmation_agent)

workflow.set_entry_point("user_input")
workflow.add_edge("user_input", "research")
workflow.add_edge("research", "schedule")
workflow.add_edge("schedule", "confirm")
workflow.add_edge("confirm", END)

app = workflow.compile()

# 4. Run the graph

if __name__ == "__main__":
    initial_state = {"user_request": "I need to book a doctor's appointment for next week."}
    final_state = app.invoke(initial_state)
    print("\n---FINAL STATE---")
    print(final_state)
