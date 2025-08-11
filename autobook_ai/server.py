from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, StreamingResponse
from pydantic import BaseModel, Field
from contextlib import asynccontextmanager
import os
import sys
import json
from typing import List, Dict, Any

# Add the project root to the Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from autobook_ai.main import AgentWorkflow

# Data model for the request, which is now just the conversation history
class InvokeRequest(BaseModel):
    messages: List[Dict[str, Any]] = Field(default_factory=list)

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
    Invokes the agent workflow with the current conversation history and streams the response.
    """
    workflow = app_state.get("workflow")
    if not workflow:
        return {"error": "Workflow not initialized. The server might be starting up."}, 503

    # The new workflow `run` method takes the conversation history directly
    return StreamingResponse(workflow.run(request.messages), media_type="text/event-stream")
