import os
import json
from langgraph.graph import StateGraph, END
from langgraph.prebuilt import ToolExecutor
from typing import TypedDict, Annotated, List, Dict, Any
from langchain_core.messages import BaseMessage, HumanMessage, AIMessage, ToolMessage
from operator import itemgetter

from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_google_genai import ChatGoogleGenerativeAI

from autobook_ai.tools import all_tools

# 1. Define the state for our agent
class AgentState(TypedDict):
    messages: Annotated[List[BaseMessage], itemgetter("messages")]

# 2. Define the Agentic Workflow as a class
class AgentWorkflow:
    def __init__(self):
        self.tool_executor = ToolExecutor(all_tools)
        self.agent = self._setup_agent()
        self.graph = self._setup_graph()

    def _setup_agent(self):
        """Sets up the main agent that can call tools."""
        prompt = ChatPromptTemplate.from_messages([
            ("system", "You are a helpful assistant named AutoBook AI. You have access to tools to help schedule appointments. Your goal is to gather information, and then create a calendar invite. Respond to the user when you have a final confirmation or need more information."),
            MessagesPlaceholder("messages"),
        ])

        llm = ChatGoogleGenerativeAI(model="gemini-pro", temperature=0)
        llm_with_tools = llm.bind_tools(all_tools)

        return prompt | llm_with_tools

    def _setup_graph(self):
        """Sets up the LangGraph workflow for the tool-using agent."""
        workflow = StateGraph(AgentState)
        workflow.add_node("agent", self.agent_node)
        workflow.add_node("tools", self.tool_executor_node)

        workflow.set_entry_point("agent")

        workflow.add_conditional_edges(
            "agent",
            self.should_call_tools,
            {
                "tools": "tools",
                "__end__": END
            }
        )

        workflow.add_edge("tools", "agent")

        return workflow.compile()

    def should_call_tools(self, state: AgentState) -> str:
        """Decides whether to call tools or end the conversation."""
        last_message = state["messages"][-1]
        if not hasattr(last_message, "tool_calls") or not last_message.tool_calls:
            return "__end__"
        return "tools"

    def agent_node(self, state: AgentState):
        """The main agent node."""
        print("---AGENT---")
        response_message = self.agent.invoke(state)
        return {"messages": [response_message]}

    def tool_executor_node(self, state: AgentState):
        """Executes the tools called by the agent."""
        print("---TOOL EXECUTOR---")
        last_message = state["messages"][-1]
        tool_calls = last_message.tool_calls

        tool_messages = []
        for tool_call in tool_calls:
            tool_output = self.tool_executor.invoke(tool_call)
            tool_messages.append(
                ToolMessage(content=str(tool_output), tool_call_id=tool_call['id'])
            )

        print(f"Tool results: {tool_messages}")
        return {"messages": tool_messages}

    def run(self, conversation: List[Dict[str, Any]]):
        # Reconstruct BaseMessage objects from the plain dicts
        history = []
        for msg in conversation:
            if msg.get('type') == 'human':
                history.append(HumanMessage(content=msg.get('content')))
            elif msg.get('type') == 'ai':
                history.append(AIMessage(content=msg.get('content')))

        # astream_events returns a stream of events, we are interested in the 'on_chat_model_stream' events
        # that contain the chunks of the response. We will yield these chunks as they come in.
        async def stream_events():
            async for event in self.graph.astream_events({"messages": history}, version="v1"):
                kind = event["event"]
                if kind == "on_chat_model_stream":
                    chunk = event["data"]["chunk"]
                    if chunk.content:
                        yield f"data: {json.dumps({'type': 'content', 'data': chunk.content})}\n\n"
                    if chunk.tool_calls:
                         yield f"data: {json.dumps({'type': 'tool_call', 'data': chunk.tool_calls})}\n\n"
                elif kind == "on_tool_end":
                    yield f"data: {json.dumps({'type': 'tool_end', 'data': event['data']['output']})}\n\n"


        return stream_events()
