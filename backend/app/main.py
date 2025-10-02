from fastapi import FastAPI, Depends, HTTPException, Header
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
import logging
from contextlib import asynccontextmanager

from app.config import settings
from app.services.file_system import FileSystemService
from app.services.rag_tools import RAGSystem

# Import MCP server
from app.mcp.combined_server import create_mcp_server

# Configure logging
logging.basicConfig(
    level=logging.INFO if settings.DEBUG else logging.WARNING,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Create shared services
file_system = FileSystemService(base_path=settings.FS_BASE_PATH)
rag_system = RAGSystem(base_path=settings.FS_BASE_PATH)

# Grant default permissions
file_system.grant_permission("mcp_agent", {
    "read": True,
    "write": True,
    "delete": False
})

# Create MCP server
mcp_server = create_mcp_server(file_system, rag_system)

# Setup FastAPI lifespan
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    logger.info("Starting application...")
    yield
    # Shutdown
    logger.info("Shutting down application...")

# Create FastAPI app
app = FastAPI(
    title=settings.APP_NAME,
    description="API for file management and RAG capabilities",
    version="1.0.0",
    lifespan=lifespan
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Simple authentication
async def verify_api_key(x_api_key: str = Header(None)):
    if settings.API_KEY and (not x_api_key or x_api_key != settings.API_KEY):
        raise HTTPException(status_code=401, detail="Invalid API Key")
    return x_api_key

# Mount MCP server if enabled
if settings.MCP_ENABLED:
    app.mount(settings.MCP_PREFIX, mcp_server.sse_app())
    logger.info(f"MCP server mounted at {settings.MCP_PREFIX}")

# Basic API routes
@app.get("/")
def root():
    return {
        "name": settings.APP_NAME,
        "version": "1.0.0",
        "mcp_enabled": settings.MCP_ENABLED
    }

@app.get("/health")
def health():
    return {"status": "ok"}

# Protected endpoint example
@app.get("/api/protected", dependencies=[Depends(verify_api_key)])
def protected_endpoint():
    return {"message": "Protected endpoint accessed successfully"}

# Include other API routes here
# app.include_router(some_router, prefix="/api", tags=["tag"])

if __name__ == "__main__":
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.DEBUG
    )