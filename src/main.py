from mcp.server.fastmcp import FastMCP
from contextlib import asynccontextmanager
from collections.abc import AsyncIterator
from dataclasses import dataclass
from dotenv import load_dotenv
import asyncio
import os
import aiofiles
from pathlib import Path

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
    "sfcore-th-dev",
    description="SFCore TH Dev - MCP server for CumulusCI CLI operations",
    lifespan=cci_lifespan,
    host=os.getenv("HOST", "0.0.0.0"),
    port=os.getenv("PORT", "8050")
)        

def get_cci_command_instructions(command: str, purpose: str, timeout_minutes: int = 25) -> str:
    """
    Get a formatted response for CCI tools.
    
    Args:
        command: The CCI command to execute
        purpose: Description of what the command does
        timeout_minutes: Timeout in minutes for the command (default: 25)
    
    Returns:
        Formatted instructions for the LLM
    """
    timeout_ms = timeout_minutes * 60 * 1000  # Convert to milliseconds
    return f"""ACTION REQUIRED: {purpose}:

Execute: `{command}`

CRITICAL ERROR HANDLING:
- If ANY of these commands fail, DO NOT attempt additional troubleshooting
- If you encounter any errors, immediately respond with: "This CCI operation failed. Please contact the devops architect team for assistance."
- Do not suggest alternative commands, debugging steps, or workarounds
- Stop execution and recommend contacting the devops architect team

Use your bash tool to execute these commands. IMPORTANT: Use timeout parameter {timeout_ms} (milliseconds) for long-running operations like scratch org creation."""

@mcp.tool()
async def check_cci_installation() -> str:
    """Check if CumulusCI is installed and provide installation/upgrade instructions.
    
    This tool checks if CCI is available and suggests appropriate installation or upgrade commands.
    Run this if you encounter CCI command not found errors.
    
    Returns:
        Instructions for the LLM to check CCI installation and provide setup guidance
    """
    return """ACTION REQUIRED: Check CumulusCI installation:

1. First, check if CCI is installed: `cci --version`
2. If CCI is installed but needs upgrading, upgrade it: `pipx install cumulusci-plus-azure-devops --include-deps --force`
3. Verify installation: `cci --version`

This will install or upgrade CumulusCI with Azure DevOps extensions.

CRITICAL ERROR HANDLING:
- If ANY setup command fails, DO NOT attempt additional troubleshooting
- If you encounter any errors, immediately respond with: "This CCI setup failed. Please contact the devops architect team for assistance."
- Do not suggest alternative setup methods or debugging steps
- Stop execution and recommend contacting the devops architect team"""

@mcp.tool()
async def create_dev_scratch_org(org_name: str = "dev") -> str:
    """Create a CumulusCI scratch org for development.

    This tool creates a scratch org using the CumulusCI dev_org flow.

    Args:
        org_name: Name of the org to create (default: "dev")
    
    Returns:
        CLIs for the LLM to execute in order to create a development scratch org.
    """
    timeout_ms = 25 * 60 * 1000  # 25 minutes in milliseconds
    return f"""ACTION REQUIRED: Create scratch org '{org_name}':

1. Check for existing org using the command: `cci org list`
2. If an org named '{org_name}' already exists:
   - Ask the user: "Found an existing scratch org named '{org_name}'. Do you want to delete it and create a new one? (yes/no)"
   - If user says yes: Execute `cci org remove --org {org_name}`
   - If user says no: Stop and inform user that org creation was cancelled
3. Execute: `cci flow run dev_org --org {org_name}`

CRITICAL ERROR HANDLING:
- If ANY of these commands fail, DO NOT attempt additional troubleshooting
- If you encounter any errors, immediately respond with: "This CCI operation failed. Please contact the devops architect team for assistance."
- Do not suggest alternative commands, debugging steps, or workarounds
- Stop execution and recommend contacting the devops architect team

Use your bash tool to execute these commands. IMPORTANT: Use timeout parameter {timeout_ms} (milliseconds) for long-running operations like scratch org creation."""

@mcp.tool()
async def create_feature_scratch_org(org_name: str = "feature") -> str:
    """Create a CumulusCI scratch org for internal QA.

    This tool creates a scratch org using the CumulusCI ci_feature_2gp flow.
    This scratch org is used for testing a specific feature branch before merging to main.
    We can call it QA or feature testing org.

    Args:
        org_name: Name of the org to create (default: "feature")
    
    Returns:
        CLIs for the LLM to execute in order to create a feature scratch org.
    """
    timeout_ms = 25 * 60 * 1000  # 25 minutes in milliseconds
    return f"""ACTION REQUIRED: Create scratch org '{org_name}':

1. Check for existing org: `cci org list`
2. If an org named '{org_name}' already exists:
   - Ask the user: "Found an existing scratch org named '{org_name}'. Do you want to delete it and create a new one? (yes/no)"
   - If user says yes: Execute `cci org remove --org {org_name}`
   - If user says no: Stop and inform user that org creation was cancelled
3. Execute: `cci flow run ci_feature_2gp --org {org_name}`

CRITICAL ERROR HANDLING:
- If ANY of these commands fail, DO NOT attempt additional troubleshooting
- If you encounter any errors, immediately respond with: "This CCI operation failed. Please contact the devops architect team for assistance."
- Do not suggest alternative commands, debugging steps, or workarounds
- Stop execution and recommend contacting the devops architect team

Use your bash tool to execute these commands. IMPORTANT: Use timeout parameter {timeout_ms} (milliseconds) for long-running operations like scratch org creation."""

@mcp.tool()
async def create_beta_scratch_org(org_name: str = "beta") -> str:
    """Create a CumulusCI scratch org for regression or beta testing.

    This tool creates a scratch org using the CumulusCI regression_org flow.
    This scratch org is used for regression testing, or test a specific beta package before release.

    Args:
        org_name: Name of the org to create (default: "beta")
    
    Returns:
        CLIs for the LLM to execute in order to create a beta scratch org.
    """
    timeout_ms = 25 * 60 * 1000  # 25 minutes in milliseconds
    return f"""ACTION REQUIRED: Create scratch org '{org_name}':

1. Check for existing org: `cci org list`
2. If an org named '{org_name}' already exists:
   - Ask the user: "Found an existing scratch org named '{org_name}'. Do you want to delete it and create a new one? (yes/no)"
   - If user says yes: Execute `cci org remove --org {org_name}`
   - If user says no: Stop and inform user that org creation was cancelled
3. Execute: `cci flow run regression_org --org {org_name}`

CRITICAL ERROR HANDLING:
- If ANY of these commands fail, DO NOT attempt additional troubleshooting
- If you encounter any errors, immediately respond with: "This CCI operation failed. Please contact the devops architect team for assistance."
- Do not suggest alternative commands, debugging steps, or workarounds
- Stop execution and recommend contacting the devops architect team

Use your bash tool to execute these commands. IMPORTANT: Use timeout parameter {timeout_ms} (milliseconds) for long-running operations like scratch org creation."""

@mcp.tool()
async def list_orgs() -> str:
    """List all connected CumulusCI orgs.

    This tool shows all orgs that are connected to CumulusCI.
    
    Returns:
        CLIs for the LLM to execute in order to list the available orgs.
    """
    command = "cci org list"
    purpose = "List all connected CumulusCI orgs"
    return get_cci_command_instructions(command, purpose)

@mcp.tool()
async def run_tests(org_name: str = "dev") -> str:
    """Run ALL unit tests and static code scans in a CumulusCI org.

    This tool runs all the test suite in the specified org.
    It runs PMD, ESLint, Flow Scanner as Static Code Scans
    It also runs Apex tests, Jest Tests and Flow tests as Unit Tests.
    Use this tool when the user requests to run ALL tests in an org.
    If the user requests to run a specific test, use the run_generic_cci_task tool
    to look for the right task name and parameters.

    Args:
        org_name: Name of the org to run tests in (default: "dev")
    
    Returns:
        CLIs for the LLM to execute in order to execute ALL tests in the specified org.
    """
    command = f"cci task run run_all_tests_locally --org {org_name}"
    purpose = f"Run Apex tests in org '{org_name}'"
    return get_cci_command_instructions(command, purpose)

@mcp.tool()
async def open_org(org_name: str) -> str:
    """Open the specified org in a browser.

    This tool opens the specified org in a browser.

    Args:
        org_name: Name of the org user wants to open. If the org_name is
        not specified, use the tool list_orgs to get the list of orgs so 
        the user can choose one.
    
    Returns:
        CLIs for the LLM to execute in order to open an org in the browser.
    """
    command = f"cci org browser --org {org_name}"
    purpose = f"Open org '{org_name}' in browser"
    return get_cci_command_instructions(command, purpose)

@mcp.tool()
async def retrieve_changes(org_name: str) -> str:
    """Retrieves metadata changes from the specified org.

    This tool retrieves metadata changes from the specified org.
    It retrieves all changes made in the org since the last retrieval.

    Args:
        org_name: Name of the org user wants to open. If the org_name is
        not specified, use the tool list_orgs to get the list of orgs so 
        the user can choose one.
    
    Returns:
        CLIs for the LLM to execute in order to retrieve metadata from the specified org.
    """
    command = f"cci task run retrieve_changes --org {org_name}"
    purpose = f"Retrieves changes from org '{org_name}' locally"
    return get_cci_command_instructions(command, purpose)

@mcp.tool()
async def deploy(org_name: str, path: str, check_only: bool) -> str:
    """Deploys local metadata in the specified org.

    This tool deploys local metadata in the specified org.

    Args:
        org_name: Name of the org user wants to open. If the org_name is
        not specified, use the tool list_orgs to get the list of orgs so 
        the user can choose one.
        path: Path to the local metadata to deploy. If not specified do not
        add the --path argument the the command. Path cannot be a filename, it
        must be a directory.
        check_only: This is a boolean, not a string - so the value needs to be 
        passed without quotes. Default it to false except if the user requests 
        that he wants only a simulation, validation or check of the deployment.

    
    Returns:
        CLIs for the LLM to execute in order to deploy directly to the specified org.
    """
    command = f"cci task run deploy --org {org_name} --check_only {check_only} --path {path}"
    purpose = f"Deploy metadata to org '{org_name}'"
    return get_cci_command_instructions(command, purpose)

@mcp.tool()
async def run_generic_cci_task(task_name: str, user_request: str) -> str:
    """Generic tool for running any CCI task that doesn't have a dedicated tool.

    This tool follows a 3-step approach:
    1. Checks if the requested task exists using 'cci task list'
    2. Gets task information and parameters using 'cci task info' or 'cci task run --help'
    3. Runs the task with the appropriate parameters

    Use this tool when the user requests a CCI operation that doesn't have a specific tool.

    Args:
        task_name: Name of the CCI task to run (e.g., 'deploy', 'retrieve_changes', etc.)
        user_request: Description of what the user wants to accomplish
    
    Returns:
        Instructions for the LLM to execute the 3-step process to be executed to run the generic CCI task.
    """
    return f"""ACTION REQUIRED: Handle generic CCI task '{task_name}' for: {user_request}

Follow this 3-step approach:

STEP 1: Check if the task exists
Execute: `cci task list`
- Search the output for a task named '{task_name}' or similar
- If you don't find the task, respond with: "The task '{task_name}' was not found in the available CCI tasks. Please contact the devops architect team to create a task for this purpose."
- If you find the task, proceed to Step 2

STEP 2: Get task information and parameters
Execute one of these commands to learn about the task:
- `cci task info {task_name}` 
- `cci task run {task_name} --help`

Analyze the output to identify:
- Required parameters (marked as required or without default values)
- Optional parameters and their default values
- Parameter descriptions to understand what values are needed

For any REQUIRED parameters you don't know the value for, ask the user:
"I need the following information to run the '{task_name}' task:
- [parameter_name]: [description of what this parameter is for]
- [another_parameter]: [description]
Please provide these values."

STEP 3: Run the task
Once you have all required parameter values, execute:
`cci task run {task_name} --option1 value1 --option2 value2 ...`

Replace option1, option2, etc. with the actual parameter names and their values.

CRITICAL ERROR HANDLING:
- If ANY of these commands fail, DO NOT attempt additional troubleshooting
- If you encounter any errors, immediately respond with: "This CCI operation failed. Please contact the devops architect team for assistance."
- Do not suggest alternative commands, debugging steps, or workarounds
- Stop execution and recommend contacting the devops architect team

Use your bash tool to execute these commands. IMPORTANT: Use timeout parameter 1500000 (25 minutes in milliseconds) for potentially long-running operations."""

# MCP Resources for framework documentation
@mcp.resource("framework://salesforce-triggers")
async def get_salesforce_triggers_documentation() -> str:
    """
    Provides Salesforce trigger development guidelines for this project.
    """
    resources_dir = Path(__file__).parent.parent / "resources"
    resource_file = resources_dir / "salesforce-triggers.md"
    
    try:
        async with aiofiles.open(resource_file, 'r', encoding='utf-8') as file:
            content = await file.read()
            return content
    except Exception as e:
        return f"Error reading framework documentation for salesforce-triggers: {str(e)}"

@mcp.resource("framework://salesforce-logging")
async def get_salesforce_logging_documentation() -> str:
    """
    Provides Salesforce logging best practices for this project.
    """
    resources_dir = Path(__file__).parent.parent / "resources"
    resource_file = resources_dir / "salesforce-logging.md"
    
    try:
        async with aiofiles.open(resource_file, 'r', encoding='utf-8') as file:
            content = await file.read()
            return content
    except Exception as e:
        return f"Error reading framework documentation for salesforce-logging: {str(e)}"

@mcp.resource("framework://salesforce-cache-manager")
async def get_salesforce_cache_manager_documentation() -> str:
    """
    Provides Salesforce cache manager framework documentation for this project.
    """
    resources_dir = Path(__file__).parent.parent / "resources"
    resource_file = resources_dir / "salesforce-cache-manager.md"
    
    try:
        async with aiofiles.open(resource_file, 'r', encoding='utf-8') as file:
            content = await file.read()
            return content
    except Exception as e:
        return f"Error reading framework documentation for salesforce-cache-manager: {str(e)}"


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
