import os
import json
from langgraph.graph import StateGraph, END
from langgraph.prebuilt import ToolExecutor
from typing import TypedDict, Annotated, List
from langchain_core.messages import BaseMessage, ToolMessage
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
            ("system",
             "You are a helpful assistant named AutoBook AI. Your goal is to help users schedule appointments. "
             "To do this, you have access to a set of tools. \n"
             "1. First, you should always use the `search_knowledge_base` tool to find out information about a service (like hours, policies, etc.).\n"
             "2. Once you have the information, you can use other tools like `check_calendar_availability`.\n"
             "3. Finally, once all details are confirmed with the user, you can use the `create_calendar_invite` tool.\n"
             "Always confirm with the user before taking a final action like creating an invite. "
             "If you don't have enough information to use a tool, ask the user for it."),
            MessagesPlaceholder(variable_name="messages"),
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

    async def run(self, messages: list):
        """Runs the workflow with the given conversation history and streams the response."""
        # The graph now directly works with the list of BaseMessage objects
        async for event in self.graph.astream_events({"messages": messages}, version="v2"):
            kind = event["event"]
            if kind == "on_chat_model_stream":
                chunk = event["data"]["chunk"]
                if chunk.content:
                    yield f"data: {json.dumps({'type': 'content', 'data': chunk.content})}\n\n"
            elif kind == "on_tool_start":
                yield f"data: {json.dumps({'type': 'tool_start', 'name': event['data']['name'], 'input': event['data']['input']})}\n\n"
            elif kind == "on_tool_end":
                yield f"data: {json.dumps({'type': 'tool_end', 'data': event['data']['output'], 'name': event['name']})}\n\n"

        # Signal the end of the stream
        yield f"data: {json.dumps({'type': 'end'})}\n\n"
