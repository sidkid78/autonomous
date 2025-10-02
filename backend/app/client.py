import asyncio
from mcp.client.session import ClientSession
from mcp.client.sse import sse_client

async def connect_to_mcp():
    # Connect to your MCP server
    url = "http://localhost:8000/mcp"
    
    # Use SSE client for HTTP connection
    async with sse_client(url) as (read, write):
        async with ClientSession(read, write) as session:
            # Initialize the connection
            await session.initialize()
            
            # List available tools
            tools = await session.list_tools()
            print(f"Available tools: {tools}")
            
            # Call a tool
            result = await session.call_tool("search_information", {
                "query": "your search query",
                "workspace_id": "default"
            })
            print(f"Search result: {result}")

if __name__ == "__main__":
    asyncio.run(connect_to_mcp())