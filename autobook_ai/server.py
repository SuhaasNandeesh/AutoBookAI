from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel, Field
from contextlib import asynccontextmanager
import os
import sys
from typing import List, Dict, Any

# Add the project root to the Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from autobook_ai.main import AgentWorkflow, load_user_profile

# Updated data model to handle conversation history
class InvokeRequest(BaseModel):
    user_request: str
    user_id: str = "default_user"
    conversation_history: List[Dict[str, Any]] = Field(default_factory=list)

# A dictionary to hold our long-lived workflow instance
app_state = {}

@asynccontextmanager
async def lifespan(app: FastAPI):
    # --- DANGER: HARDCODED API KEY ---
    API_KEY = "AIzaSyDovZgWFH0wbFZBqMQZblkf71owGh5yFhk"
    os.environ["GOOGLE_API_KEY"] = API_KEY

    print("Loading Agent Workflow...")
    app_state["workflow"] = AgentWorkflow()
    print("Workflow loaded successfully.")

    yield

    app_state.clear()
    print("Workflow resources cleaned up.")

# Create the FastAPI app with the lifespan manager
app = FastAPI(lifespan=lifespan)

# Mount the static directory to serve frontend files
app.mount("/static", StaticFiles(directory="static"), name="static")

@app.get("/")
async def read_root():
    """Serves the main index.html file."""
    return FileResponse('static/index.html')

@app.post("/invoke")
async def invoke_workflow(request: InvokeRequest):
    """
    Invokes the agent workflow with the current conversation state.
    """
    workflow = app_state.get("workflow")
    if not workflow:
        return {"error": "Workflow not initialized. The server might be starting up."}, 503

    # Load the user profile
    user_profile = load_user_profile(request.user_id)

    # Reconstruct BaseMessage objects from the plain dicts sent by the client
    # This is a simplified reconstruction for this example.
    # A more robust solution would handle different message types.
    from langchain_core.messages import HumanMessage, AIMessage
    history = []
    for msg in request.conversation_history:
        if msg.get('type') == 'human':
            history.append(HumanMessage(content=msg.get('content')))
        elif msg.get('type') == 'ai':
            history.append(AIMessage(content=msg.get('content')))

    # Set up the initial state for the workflow run
    initial_state = {
        "user_request": request.user_request,
        "user_profile": user_profile,
        "conversation_history": history
    }

    # Run the workflow
    final_state = workflow.run(initial_state)

    # The client needs a serializable version of the state
    # We convert BaseMessage objects back to dicts
    if 'conversation_history' in final_state:
        final_state['conversation_history'] = [
            {'type': msg.type, 'content': msg.content}
            for msg in final_state['conversation_history']
        ]

    return final_state
