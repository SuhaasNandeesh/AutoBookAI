import os
import json
from langgraph.graph import StateGraph, END
from typing import TypedDict, Dict, Any

from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain_google_genai import ChatGoogleGenerativeAI

from autobook_ai.rag import create_retriever, create_rag_chain

# 1. Define the state for our graph, now including user profile
class AppState(TypedDict):
    """
    The state of our application graph.
    """
    user_request: str
    user_profile: Dict[str, Any]
    research_findings: str
    schedule: str
    confirmation: str

# 2. Helper function to load user profiles
def load_user_profile(user_id: str) -> Dict[str, Any]:
    """
    Loads a user profile from a JSON file.
    """
    profile_path = f"user_profiles/{user_id}.json"
    if not os.path.exists(profile_path):
        return {} # Return an empty profile if not found

    with open(profile_path, 'r') as f:
        return json.load(f)

# 3. Define the Agentic Workflow as a class
class AgentWorkflow:
    def __init__(self):
        """
        Initializes the workflow, including all agent chains and the graph.
        """
        self.rag_chain = self._setup_rag_chain()
        self.scheduling_chain = self._setup_scheduling_chain()
        self.confirmation_chain = self._setup_confirmation_chain()
        self.graph = self._setup_graph()

    def _setup_rag_chain(self):
        retriever = create_retriever()
        rag_chain = create_rag_chain(retriever)
        return rag_chain

    def _setup_scheduling_chain(self):
        prompt_template = """Based on the user's request, their profile, and the following research, create a concrete booking proposal.
        Use the user's profile to inform your suggestions (e.g., mention their preferred city or cuisine).
        If you have enough information, suggest a specific time and action.
        If information is missing, state what is needed to proceed.

        User Profile: {user_profile}
        User Request: {user_request}
        Research Findings: {research_findings}

        Proposed Schedule:"""

        prompt = ChatPromptTemplate.from_template(prompt_template)
        llm = ChatGoogleGenerativeAI(model="gemini-pro", temperature=0)
        chain = prompt | llm | StrOutputParser()
        return chain

    def _setup_confirmation_chain(self):
        prompt_template = """You are a friendly assistant. Based on the following proposed schedule, write a short, friendly confirmation message for the user.
        Make it sound final and reassuring.

        Proposed Schedule: {schedule}

        Confirmation Message:"""

        prompt = ChatPromptTemplate.from_template(prompt_template)
        llm = ChatGoogleGenerativeAI(model="gemini-pro", temperature=0.1)
        chain = prompt | llm | StrOutputParser()
        return chain

    def _setup_graph(self):
        workflow = StateGraph(AppState)
        workflow.add_node("user_input", self.user_input_agent)
        workflow.add_node("research", self.research_agent)
        workflow.add_node("schedule", self.scheduling_agent)
        workflow.add_node("confirm", self.confirmation_agent)
        workflow.set_entry_point("user_input")
        workflow.add_edge("user_input", "research")
        workflow.add_edge("research", "schedule")
        workflow.add_edge("schedule", "confirm")
        workflow.add_edge("confirm", END)
        return workflow.compile()

    def user_input_agent(self, state: AppState):
        print("---USER INPUT AGENT---")
        print(f"User request: {state['user_request']}")
        # The user profile is already loaded by the server and is in the state.
        # This agent could be enhanced to greet the user by name.
        return state

    def research_agent(self, state: AppState):
        print("---RESEARCH AGENT---")
        # The RAG chain doesn't need the user profile directly,
        # but the scheduling agent will.
        user_request = state["user_request"]
        print(f"Performing research for: {user_request}")
        findings = self.rag_chain.invoke(user_request)
        print(f"Research findings: {findings}")
        return {"research_findings": findings}

    def scheduling_agent(self, state: AppState):
        print("---SCHEDULING AGENT---")
        print("Generating schedule with personalization...")
        schedule = self.scheduling_chain.invoke({
            "user_profile": state["user_profile"],
            "user_request": state["user_request"],
            "research_findings": state["research_findings"]
        })
        print(f"Proposed schedule: {schedule}")
        return {"schedule": schedule}

    def confirmation_agent(self, state: AppState):
        print("---CONFIRMATION AGENT---")
        print("Generating confirmation...")
        confirmation = self.confirmation_chain.invoke({"schedule": state["schedule"]})
        print(f"Confirmation: {confirmation}")
        return {"confirmation": confirmation}

    def run(self, initial_state: dict):
        return self.graph.invoke(initial_state)
