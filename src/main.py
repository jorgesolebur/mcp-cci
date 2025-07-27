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
async def create_scratch_org(org_type: str, org_name: str = None) -> str:
    """Create a CumulusCI scratch org of the specified type.

    This tool creates a scratch org using the appropriate CumulusCI flow based on the org type.

    Args:
        org_type: Type of org to create. Valid values: "dev", "feature", "beta"
                 - "dev": Creates a development org using dev_org flow
                 - "feature": Creates a feature testing/QA org using ci_feature_2gp flow, used if the user wants to do QA testing of a feature
                 - "beta": Creates a regression/beta testing org using regression_org flow, used if the user wants to do regression testing
        org_name: Name of the org to create. If not provided, defaults based on org_type
                 (dev -> "dev", feature -> "feature", beta -> "beta")
    
    Returns:
        CLIs for the LLM to execute in order to create the specified scratch org.
    """
    # Validate org_type and set defaults
    flow_mapping = {
        "dev": "dev_org",
        "feature": "ci_feature_2gp", 
        "beta": "regression_org"
    }
    
    if org_type not in flow_mapping:
        return f"ERROR: Invalid org_type '{org_type}'. Valid values are: dev, feature, beta"
    
    # Set default org name if not provided
    if org_name is None:
        org_name = org_type
    
    flow_name = flow_mapping[org_type]
    timeout_ms = 25 * 60 * 1000  # 25 minutes in milliseconds
    
    org_type_descriptions = {
        "dev": "development org",
        "feature": "feature testing/QA org", 
        "beta": "regression/beta testing org"
    }
    
    return f"""ACTION REQUIRED: Create {org_type_descriptions[org_type]} '{org_name}':

1. Check for existing org: `cci org list`
2. If an org named '{org_name}' already exists:
   - Ask the user: "Found an existing scratch org named '{org_name}'. Do you want to delete it and create a new one? (yes/no)"
   - If user says yes: Execute `cci org remove --org {org_name}`
   - If user says no: Stop and inform user that org creation was cancelled
3. Execute: `cci flow run {flow_name} --org {org_name}`

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
    """Run ALL Apex unit tests and static code scans in a CumulusCI org.

    This tool runs all the test suite in the specified org.
    It runs PMD, ESLint, Flow Scanner as Static Code Scans
    It also runs Apex tests, Jest Tests and Flow tests as Unit Tests.
    Use this tool when the user requests to run ALL tests in an org.
    If the user requests to run a specific test, use the run_generic_cci_task tool
    to look for the right task name and options to run specific tests.

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

@mcp.tool()
async def validate_changes(target_org: str = "feature") -> str:
    """Validate developer changes locally before creating a PR.

    This tool runs a simulation of the build process to validate changes locally.
    It performs static code scans, creates a package, and posts commit status.
    This is the validation process developers should run before creating their PR.

    Args:
        target_org: Name of the target org for package creation (default: "feature")
    
    Returns:
        Instructions for the LLM to execute the validation process sequentially.
    """
    timeout_ms = 25 * 60 * 1000  # 25 minutes in milliseconds
    
    return f"""ACTION REQUIRED: Validate developer changes locally before PR creation:

Execute these steps SEQUENTIALLY. If any step fails, STOP and do not continue to next step.

=== STEP 1: STATIC CODE SCAN ===
Execute these commands in order. If ANY fail, developer must fix the issues and run validation again:

1.1. PMD Analysis:
`cci task run run_code_analyser --rule_selector pmd --junit_file test-results-pmd/pmd-report.xml`

1.2. ESLint Analysis:
`cci task run run_code_analyser --rule_selector eslint --junit_file test-results-eslint/eslint-report.xml`

1.3. Salesforce Flow Scanner:
`cci task run run_sf_flow_scan`

If any of the above commands fail, respond with: "Static code scan failed. Please review and fix the reported issues, then run validation again."

=== STEP 2: CREATE PACKAGE ===
2.1. Create package (try with {target_org} first):
`cci flow run build_feature_test_package --org {target_org}`

If this command fails because a package could not be upgraded, retry with:
`cci flow run build_feature_test_package --org snapshot`

2.2. From the command output above, look for a packageVersionId that starts with "04t" (there will be only one).
Store this packageVersionId - you'll need it for Step 3.

=== STEP 3: POST COMMIT STATUS ===
3.1. Get the current branch's last commit ID:
`git rev-parse HEAD`

3.2. Post commit status with the package version ID from Step 2.2:
`cci task run ado_post_commit_status --commit_id <COMMIT_ID> --package_version_id <PACKAGE_VERSION_ID>`

Replace <COMMIT_ID> with the commit ID from step 3.1 and <PACKAGE_VERSION_ID> with the ID from step 2.2.

CRITICAL ERROR HANDLING:
- Execute steps SEQUENTIALLY - do not proceed if any step fails
- If ANY command fails, DO NOT attempt additional troubleshooting
- If you encounter any errors, immediately respond with: "This CCI operation failed. Please contact the devops architect team for assistance."
- Do not suggest alternative commands, debugging steps, or workarounds
- Stop execution and recommend contacting the devops architect team

Use your bash tool to execute these commands. IMPORTANT: Use timeout parameter {timeout_ms} (milliseconds) for long-running operations."""

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
