from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel
from contextlib import asynccontextmanager
import os
import sys

# Add the project root to the Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from autobook_ai.main import AgentWorkflow

# Data model for the request body
class InvokeRequest(BaseModel):
    user_request: str

# A dictionary to hold our long-lived workflow instance
app_state = {}

@asynccontextmanager
async def lifespan(app: FastAPI):
    # --- DANGER: HARDCODED API KEY ---
    # This is a workaround for an issue with creating .env files in this environment.
    # In a real-world application, NEVER hardcode secrets like this.
    # Use environment variables or a proper secrets management system.
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
    """
    Serves the main index.html file.
    """
    return FileResponse('static/index.html')

@app.post("/invoke")
async def invoke_workflow(request: InvokeRequest):
    """
    Invokes the agent workflow with a user request.
    """
    workflow = app_state.get("workflow")
    if not workflow:
        return {"error": "Workflow not initialized. The server might be starting up."}, 503

    initial_state = {"user_request": request.user_request}
    final_state = workflow.run(initial_state)

    return final_state
