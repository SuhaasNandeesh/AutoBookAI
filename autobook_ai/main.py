import os
import json
from langgraph.graph import StateGraph, END
from typing import TypedDict, Dict, Any, List
from langchain_core.messages import BaseMessage, HumanMessage, AIMessage

from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain_google_genai import ChatGoogleGenerativeAI

from autobook_ai.rag import create_retriever, create_rag_chain

# 1. Evolved AppState for conversational flow
class AppState(TypedDict):
    user_request: str
    user_profile: Dict[str, Any]
    conversation_history: List[BaseMessage]
    research_findings: str
    schedule: str
    confirmation: str
    next_action: str

# 2. Helper function to load user profiles
def load_user_profile(user_id: str) -> Dict[str, Any]:
    profile_path = f"user_profiles/{user_id}.json"
    if not os.path.exists(profile_path):
        return {}
    with open(profile_path, 'r') as f:
        return json.load(f)

# 3. Define the Agentic Workflow as a class
class AgentWorkflow:
    def __init__(self):
        self.rag_chain = self._setup_rag_chain()
        self.scheduling_chain = self._setup_scheduling_chain()
        self.confirmation_chain = self._setup_confirmation_chain()
        self.routing_chain = self._setup_routing_chain()
        self.clarification_chain = self._setup_clarification_chain()
        self.graph = self._setup_graph()

    def _setup_rag_chain(self):
        retriever = create_retriever()
        return create_rag_chain(retriever)

    def _setup_scheduling_chain(self):
        prompt_template = """Based on the user's request, their profile, and the following research, create a concrete booking proposal.
        Use the user's profile to inform your suggestions (e.g., mention their preferred city or cuisine).
        If you have enough information, suggest a specific time and action.
        If information is missing, state what is needed to proceed.

        User Profile: {user_profile}
        Conversation History: {conversation_history}
        User Request: {user_request}
        Research Findings: {research_findings}

        Proposed Schedule:"""
        prompt = ChatPromptTemplate.from_template(prompt_template)
        llm = ChatGoogleGenerativeAI(model="gemini-pro", temperature=0)
        return prompt | llm | StrOutputParser()

    def _setup_confirmation_chain(self):
        prompt_template = """You are a friendly assistant. Based on the following proposed schedule, write a short, friendly confirmation message for the user.
        Make it sound final and reassuring.

        Proposed Schedule: {schedule}

        Confirmation Message:"""
        prompt = ChatPromptTemplate.from_template(prompt_template)
        llm = ChatGoogleGenerativeAI(model="gemini-pro", temperature=0.1)
        return prompt | llm | StrOutputParser()

    def _setup_routing_chain(self):
        prompt_template = """Given the conversation history and research findings, decide the next action.
        Actions must be one of: SCHEDULE, CLARIFY.
        - If the findings provide enough information to fulfill the user's request, choose SCHEDULE.
        - If the findings are ambiguous or insufficient, choose CLARIFY.

        Conversation History: {conversation_history}
        Research Findings: {research_findings}
        Next Action:"""
        prompt = ChatPromptTemplate.from_template(prompt_template)
        llm = ChatGoogleGenerativeAI(model="gemini-pro", temperature=0)
        return prompt | llm | StrOutputParser()

    def _setup_clarification_chain(self):
        prompt_template = """Based on the conversation history and ambiguous research, ask a clear, concise question to the user.
        Conversation History: {conversation_history}
        Research Findings: {research_findings}
        Clarifying Question:"""
        prompt = ChatPromptTemplate.from_template(prompt_template)
        llm = ChatGoogleGenerativeAI(model="gemini-pro", temperature=0)
        return prompt | llm | StrOutputParser()

    def _setup_graph(self):
        workflow = StateGraph(AppState)
        workflow.add_node("user_input", self.user_input_agent)
        workflow.add_node("research", self.research_agent)
        workflow.add_node("router", self.route_after_research)
        workflow.add_node("clarify", self.clarification_agent)
        workflow.add_node("schedule", self.scheduling_agent)
        workflow.add_node("confirm", self.confirmation_agent)

        workflow.set_entry_point("user_input")
        workflow.add_edge("user_input", "research")
        workflow.add_edge("research", "router")

        # This is where the conditional logic is implemented
        workflow.add_conditional_edges(
            "router",
            self.should_continue,
            {
                "CLARIFY": "clarify",
                "SCHEDULE": "schedule"
            }
        )

        workflow.add_edge("clarify", END) # Stop and wait for user's next input
        workflow.add_edge("schedule", "confirm")
        workflow.add_edge("confirm", END)

        return workflow.compile()

    def should_continue(self, state: AppState) -> str:
        """The routing logic for the conditional edge."""
        return state["next_action"]

    def user_input_agent(self, state: AppState):
        print("---USER INPUT AGENT---")
        user_request = state["user_request"]
        history = state.get("conversation_history", [])
        history.append(HumanMessage(content=user_request))
        print(f"User request: {user_request}")
        return {"conversation_history": history, "user_request": user_request}

    def research_agent(self, state: AppState):
        print("---RESEARCH AGENT---")
        user_request = state["user_request"]
        print(f"Performing research for: {user_request}")
        findings = self.rag_chain.invoke(user_request)
        print(f"Research findings: {findings}")
        return {"research_findings": findings}

    def route_after_research(self, state: AppState):
        print("---ROUTER---")
        next_action = self.routing_chain.invoke({
            "conversation_history": state["conversation_history"],
            "research_findings": state["research_findings"]
        }).strip().upper() # Ensure it's uppercase
        print(f"Next action decided: {next_action}")
        return {"next_action": next_action}

    def clarification_agent(self, state: AppState):
        print("---CLARIFICATION AGENT---")
        clarifying_question = self.clarification_chain.invoke({
            "conversation_history": state["conversation_history"],
            "research_findings": state["research_findings"]
        })
        print(f"Asking user: {clarifying_question}")
        history = state["conversation_history"]
        history.append(AIMessage(content=clarifying_question))
        return {"conversation_history": history, "confirmation": clarifying_question}

    def scheduling_agent(self, state: AppState):
        print("---SCHEDULING AGENT---")
        print("Generating schedule with personalization...")
        schedule = self.scheduling_chain.invoke({
            "user_profile": state["user_profile"],
            "conversation_history": state["conversation_history"],
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
        history = state["conversation_history"]
        history.append(AIMessage(content=confirmation))
        return {"conversation_history": history, "confirmation": confirmation}

    def run(self, initial_state: dict):
        return self.graph.invoke(initial_state)
