from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from typing import List, Tuple

# Import the agent components we've been working on
from app.models.schemas import WorkflowSelection, AgentResponse, WorkflowRequest, ToolDefinition
from app.core.llm_client import get_llm_client
from google.genai import types as genai_types
from app.personas.agent_personas import agent_personas
from app.workflows.autonomous_agent import execute, generate_agent_context, format_action_content
# Import a tool for the agent to use
from app.services.file_system import FileSystemService
from app.config import settings 



app = FastAPI()

# --- 1. Enable CORS ---
# This allows your frontend to make requests to your backend
origins = [
    "http://localhost:3000", # Next.js default port
    "http://localhost:3001", # Another common port for Next.js
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- 2. Define API Models ---
# Although AgentResponse is in schemas.py, we define a specific
# response model for this endpoint for clarity.
from pydantic import BaseModel

class AgentExecutionResponse(BaseModel):
    final_response: str
    intermediate_steps: List[AgentResponse]

# --- 3. Define the Agent Endpoint ---
@app.post("/api/v1/agent/execute", response_model=AgentExecutionResponse)
async def execute_agent_workflow(request: WorkflowRequest):
    """
    Endpoint to execute the autonomous agent workflow.
    Receives a user query and returns the agent's final response and trace.
    """
    user_query = request.user_query

    file_system_service = FileSystemService(base_path=".")
    # a. Define the tools available to the agent for this endpoint
    available_tools = [
        ToolDefinition(
            name="write_file",
            description="Writes content to a local file in the `backend/` directory. Overwrites the file if it exists.",
            parameters={
                "type": "object",
                "properties": {
                    "path": {"type": "string", "description": "The relative path of the file to write."},
                    "content": {"type": "string", "description": "The text content to write into the file."}
                },
                "required": ["path", "content"]
            },
            # We pass the actual async function to be executed
            function=file_system_service.write_file
        )
    ]

    # b. Load the agent personas
    personas = agent_personas
    workflow_selection = WorkflowSelection(personas=personas)

    # c. Execute the agent workflow
    final_response, intermediate_steps = await execute(
        workflow_selection=workflow_selection,
        user_query=user_query,
        max_iterations=5,
        available_tools=available_tools
    )

    # d. Return the results
    return AgentExecutionResponse(
        final_response=final_response,
        intermediate_steps=intermediate_steps
    )

# --- Keep a root endpoint for basic health checks ---
@app.get("/")
def read_root():
    return {"status": "Autonomous agent backend is running"}





























# import logging
# from contextlib import asynccontextmanager

# from app.config import settings
# from app.services.file_system import FileSystemService
# from app.services.rag_tools import RAGSystem

# # Import MCP server
# from app.mcp.combined_server import create_mcp_server

# # Configure logging
# logging.basicConfig(
#     level=logging.INFO if settings.DEBUG else logging.WARNING,
#     format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
# )
# logger = logging.getLogger(__name__)

# # Create shared services
# file_system = FileSystemService(base_path=settings.FS_BASE_PATH)
# rag_system = RAGSystem(base_path=settings.FS_BASE_PATH)

# # Grant default permissions
# file_system.grant_permission("mcp_agent", {
#     "read": True,
#     "write": True,
#     "delete": False
# })

# # Create MCP server
# mcp_server = create_mcp_server(file_system, rag_system)

# # Setup FastAPI lifespan
# @asynccontextmanager
# async def lifespan(app: FastAPI):
#     # Startup
#     logger.info("Starting application...")
#     yield
#     # Shutdown
#     logger.info("Shutting down application...")

# # Create FastAPI app
# app = FastAPI(
#     title=settings.APP_NAME,
#     description="API for file management and RAG capabilities",
#     version="1.0.0",
#     lifespan=lifespan
# )

# # Add CORS middleware
# app.add_middleware(
#     CORSMiddleware,
#     allow_origins=settings.ALLOWED_ORIGINS,
#     allow_credentials=True,
#     allow_methods=["*"],
#     allow_headers=["*"],
# )

# # Simple authentication
# async def verify_api_key(x_api_key: str = Header(None)):
#     if settings.API_KEY and (not x_api_key or x_api_key != settings.API_KEY):
#         raise HTTPException(status_code=401, detail="Invalid API Key")
#     return x_api_key

# # Mount MCP server if enabled
# if settings.MCP_ENABLED:
#     app.mount(settings.MCP_PREFIX, mcp_server.sse_app())
#     logger.info(f"MCP server mounted at {settings.MCP_PREFIX}")

# # Basic API routes
# @app.get("/")
# def root():
#     return {
#         "name": settings.APP_NAME,
#         "version": "1.0.0",
#         "mcp_enabled": settings.MCP_ENABLED
#     }

# @app.get("/health")
# def health():
#     return {"status": "ok"}

# # Protected endpoint example
# @app.get("/api/protected", dependencies=[Depends(verify_api_key)])
# def protected_endpoint():
#     return {"message": "Protected endpoint accessed successfully"}

# # Include other API routes here
# # app.include_router(some_router, prefix="/api", tags=["tag"])

# if __name__ == "__main__":
#     uvicorn.run(
#         "app.main:app",
#         host="0.0.0.0",
#         port=8000,
#         reload=settings.DEBUG
#     )