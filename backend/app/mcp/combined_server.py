from mcp.server.fastmcp import FastMCP, Context
from contextlib import asynccontextmanager
from collections.abc import AsyncIterator
from dataclasses import dataclass
import os
import json
from typing import List, Dict, Any, Optional
import logging

from app.services.file_system import FileSystemService
from app.services.rag_tools import RAGSystem, WebScraperTool, RAGRetrieverTool

logger = logging.getLogger(__name__)

@dataclass
class AppContext:
    file_system: FileSystemService
    rag_system: RAGSystem

def create_mcp_server(file_system: FileSystemService, rag_system: RAGSystem) -> FastMCP:
    """
    Create a combined MCP server with file system and RAG capabilities
    
    Args:
        file_system: The file system service
        rag_system: The RAG system
        
    Returns:
        A configured FastMCP server
    """
    # Create MCP server with dependencies
    mcp = FastMCP(
        "Build5Assistant",
        dependencies=[
            "requests",
            "bs4",
            "sentence-transformers",
            "scikit-learn",
            "numpy"
        ],
        instructions="""
        This server provides access to file management and RAG capabilities for Build5.
        
        Available resources:
        - files://list/{directory} - List files in a directory
        - files://read/{file_path} - Read a file's content
        - files://metadata/{file_path} - Get file metadata
        - rag://workspaces/{workspace_id}/files - List files in a RAG workspace
        - rag://workspaces/{workspace_id}/context/{query} - Get context for a query
        
        Available tools:
        - scrape_url - Scrape a web page
        - search_information - Search for information
        - create_workspace - Create a RAG workspace
        - get_weather - Get current weather
        """
    )
    
    # Set up lifespan management
    @asynccontextmanager
    async def app_lifespan(server: FastMCP) -> AsyncIterator[AppContext]:
        """Manage application lifecycle with type-safe context"""
        try:
            # Share existing services
            yield AppContext(file_system=file_system, rag_system=rag_system)
        finally:
            # No cleanup needed since we're using shared services
            pass
    
    # Pass lifespan to server
    mcp = FastMCP("Build5Assistant", lifespan=app_lifespan)
    
    # -- File System Resources --
    
    @mcp.resource("files://list/{directory}")
    def list_directory_files(directory: str) -> str:
        """List files in a directory"""
        fs = mcp.current_context.lifespan_context.file_system
        try:
            files = fs.list_files("mcp_agent", directory)
            return "\n".join(files)
        except Exception as e:
            return f"Error listing directory: {str(e)}"
    
    @mcp.resource("files://read/{file_path}")
    async def read_file_content(file_path: str) -> str:
        """Read the content of a file"""
        fs = mcp.current_context.lifespan_context.file_system
        try:
            content = await fs.read_file("mcp_agent", file_path)
            return content
        except Exception as e:
            return f"Error reading file: {str(e)}"
    
    @mcp.resource("files://metadata/{file_path}")
    def get_file_info(file_path: str) -> str:
        """Get metadata about a file"""
        fs = mcp.current_context.lifespan_context.file_system
        try:
            metadata = fs.get_file_metadata("mcp_agent", file_path)
            return json.dumps(metadata, default=str, indent=2)
        except Exception as e:
            return f"Error getting file metadata: {str(e)}"
    
    # -- RAG Resources --
    
    @mcp.resource("rag://workspaces/{workspace_id}/files")
    def list_workspace_files(workspace_id: str) -> str:
        """List files in a RAG workspace"""
        rag_system = mcp.current_context.lifespan_context.rag_system
        try:
            result = rag_system.list_workspace_files(workspace_id)
            return json.dumps(result, indent=2)
        except Exception as e:
            return f"Error listing workspace files: {str(e)}"
    
    @mcp.resource("rag://workspaces/{workspace_id}/context/{query}")
    def get_rag_context(workspace_id: str, query: str) -> str:
        """Get RAG context for a query"""
        rag_system = mcp.current_context.lifespan_context.rag_system
        try:
            result = rag_system.retrieve_information(
                workspace_id=workspace_id,
                query=query,
                use_semantic=True,
                max_results=5
            )
            
            if result["status"] == "success":
                return result["formatted_context"]
            else:
                return result["message"]
        except Exception as e:
            return f"Error retrieving information: {str(e)}"
    
    # -- Tools --
    
    @mcp.tool()
    async def scrape_url(url: str, workspace_id: str = "default", ctx: Context = None) -> str:
        """Scrape a web page and save its content to a workspace"""
        if ctx:
            await ctx.info(f"Scraping URL: {url}")
        
        rag_system = mcp.current_context.lifespan_context.rag_system
        try:
            result = rag_system.scrape_url(workspace_id, url)
            
            if result["status"] == "success":
                if ctx:
                    await ctx.info(f"Successfully scraped URL: {url}")
                return json.dumps(result, indent=2)
            else:
                if ctx:
                    await ctx.error(f"Failed to scrape URL: {url}")
                return json.dumps(result, indent=2)
        except Exception as e:
            if ctx:
                await ctx.error(f"Error scraping URL: {str(e)}")
            return json.dumps({"status": "error", "message": str(e)}, indent=2)
    
    @mcp.tool()
    async def search_information(
        query: str, 
        workspace_id: str = "default", 
        use_semantic: bool = True,
        max_results: int = 5,
        ctx: Context = None
    ) -> str:
        """Search for information in a workspace based on a query"""
        if ctx:
            await ctx.info(f"Searching for: '{query}' in workspace '{workspace_id}'")
        
        rag_system = mcp.current_context.lifespan_context.rag_system
        try:
            result = rag_system.retrieve_information(
                workspace_id=workspace_id,
                query=query,
                use_semantic=use_semantic,
                max_results=max_results
            )
            
            if ctx:
                if result["status"] == "success":
                    await ctx.info(f"Found {result['result_count']} results")
                else:
                    await ctx.info(result["message"])
            
            return json.dumps(result, indent=2)
        except Exception as e:
            if ctx:
                await ctx.error(f"Error searching for information: {str(e)}")
            return json.dumps({"status": "error", "message": str(e)}, indent=2)
    
    @mcp.tool()
    def create_workspace(workspace_id: str = None, ctx: Context = None) -> str:
        """Create a new RAG workspace"""
        rag_system = mcp.current_context.lifespan_context.rag_system
        try:
            created_workspace_id = rag_system.create_workspace(workspace_id)
            
            if ctx:
                ctx.info(f"Created workspace: {created_workspace_id}")
            
            return json.dumps({
                "status": "success",
                "workspace_id": created_workspace_id,
                "message": f"Workspace created successfully with ID: {created_workspace_id}"
            }, indent=2)
        except Exception as e:
            if ctx:
                ctx.error(f"Error creating workspace: {str(e)}")
            return json.dumps({"status": "error", "message": str(e)}, indent=2)
    
    @mcp.tool()
    def get_weather(location: str, units: str = 'metric', ctx: Context = None) -> str:
        """Get current weather for a location"""
        if ctx:
            ctx.info(f"Getting weather for: {location}")
        
        scraper = mcp.current_context.lifespan_context.rag_system.scraper
        try:
            result = scraper.get_weather_data(location, units)
            
            if "error" in result:
                if ctx:
                    ctx.error(f"Error getting weather: {result['error']}")
            else:
                if ctx:
                    ctx.info(f"Successfully retrieved weather for {location}")
            
            return json.dumps(result, indent=2)
        except Exception as e:
            if ctx:
                ctx.error(f"Error getting weather: {str(e)}")
            return json.dumps({"error": str(e)}, indent=2)
    
    # Return the configured server
    return mcp