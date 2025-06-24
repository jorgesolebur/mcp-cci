from mcp.server.fastmcp import FastMCP, Context
from contextlib import asynccontextmanager
from collections.abc import AsyncIterator
from dataclasses import dataclass
from dotenv import load_dotenv
import asyncio
import os

from utils import run_cci_command

load_dotenv()

# Create a dataclass for our application context
@dataclass
class CCIContext:
    """Context for the CCI MCP server."""
    pass

@asynccontextmanager
async def cci_lifespan(server: FastMCP) -> AsyncIterator[CCIContext]:
    """
    Manages the CCI server lifecycle.
    
    Args:
        server: The FastMCP server instance
        
    Yields:
        CCIContext: The context for CCI operations
    """
    try:
        yield CCIContext()
    finally:
        # No explicit cleanup needed
        pass

# Initialize FastMCP server
mcp = FastMCP(
    "mcp-cci",
    description="MCP server for CumulusCI CLI operations",
    lifespan=cci_lifespan,
    host=os.getenv("HOST", "0.0.0.0"),
    port=os.getenv("PORT", "8050")
)        

@mcp.tool()
async def create_scratch_org(org_name: str = "dev") -> str:
    """Create a CumulusCI scratch org for development.

    This tool creates a new scratch org using the CumulusCI dev_org flow.
    The org will be configured with the default settings for development work.

    Args:
        org_name: Name of the org to create (default: "dev")
    """
    try:
        result = await run_cci_command(f"flow run dev_org --org {org_name}")
        return result
    except Exception as e:
        return f"Error creating scratch org: {str(e)}"

async def main():
    transport = os.getenv("TRANSPORT", "sse")
    if transport == 'sse':
        # Run the MCP server with sse transport
        await mcp.run_sse_async()
    else:
        # Run the MCP server with stdio transport
        await mcp.run_stdio_async()

if __name__ == "__main__":
    asyncio.run(main())
