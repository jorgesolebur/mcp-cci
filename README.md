<h1 align="center">SFCore TH Dev: CumulusCI Integration for AI Agents</h1>

An implementation of the [Model Context Protocol (MCP)](https://modelcontextprotocol.io) server integrated with [CumulusCI](https://cumulusci.org) for providing AI agents with Salesforce development capabilities.

This server enables AI agents to interact with CumulusCI commands without developers needing to remember complex CLI syntax.

## Overview

This project demonstrates how to build an MCP server that enables AI agents to execute CumulusCI operations for Salesforce development workflows. It serves as a foundation for creating more comprehensive CCI integrations.

The implementation follows the best practices laid out by Anthropic for building MCP servers, allowing seamless integration with any MCP-compatible client.

## Features

The server currently provides one essential CCI operation:

1. **`create_scratch_org`**: Create a new scratch org using the CCI dev_org flow

## Prerequisites

- Python 3.12+
- Access to a Salesforce org (Dev Hub for scratch orgs)
- Docker if running the MCP server as a container (recommended)

## Environment Setup

The MCP server provides CCI installation checking and setup instructions. When you encounter CCI command not found errors, use the `check_cci_installation` tool which will guide you through:

```bash
# Check if CCI is installed
cci version

# Install CCI if not present
pipx install cumulusci-plus-azure-devops

# Upgrade CCI if needed
pipx install cumulusci-plus-azure-devops --force
```

## Installation

### Using uv

1. Install uv if you don't have it:
   ```bash
   pip install uv
   ```

2. Clone this repository:
   ```bash
   git clone <your-repo-url>
   cd sfcore-th-dev
   ```

3. Install dependencies:
   ```bash
   uv pip install -e .
   ```

4. Ensure CumulusCI is installed and configured:
   ```bash
   pip install cumulusci
   cci org connect <your-dev-hub>
   ```

### Using Docker (Recommended)

1. Build the Docker image:
   ```bash
   docker build -t ghcr.io/jorgesolebur/mcp-sfcore-th-dev:latest --build-arg PORT=8050 .
   ```

2. Push to GitHub Container Registry:
   ```bash
   docker push ghcr.io/jorgesolebur/mcp-sfcore-th-dev:latest
   ```

   Note: You'll need to authenticate with GitHub Container Registry first:
   ```bash
   echo $GITHUB_TOKEN | docker login ghcr.io -u jorgesolebur --password-stdin
   ```

## Configuration

The following environment variables can be configured in your `.env` file:

| Variable | Description | Default |
|----------|-------------|---------|
| `TRANSPORT` | Transport protocol (sse or stdio) | `sse` |
| `HOST` | Host to bind to when using SSE transport | `0.0.0.0` |
| `PORT` | Port to listen on when using SSE transport | `8050` |

The server relies on CumulusCI being properly configured on the system where it runs.

## Running the Server

### Using uv

#### SSE Transport

```bash
# Set TRANSPORT=sse in .env then:
uv run src/main.py
```

The MCP server will run as an API endpoint that you can connect to with the config shown below.

#### Stdio Transport

With stdio, the MCP client itself can spin up the MCP server, so nothing to run at this point.

### Using Docker

#### SSE Transport

```bash
docker run -d -p 8050:8050 ghcr.io/jorgesolebur/mcp-sfcore-th-dev:latest
```

The MCP server will run as an API endpoint within the container.

#### Stdio Transport

With stdio, the MCP client itself can spin up the MCP server container, so nothing to run at this point.

## Integration with MCP Clients

### SSE Configuration

Once you have the server running with SSE transport, you can connect to it using this configuration:

```json
{
  "mcpServers": {
    "sfcore-th-dev": {
      "transport": "sse",
      "url": "http://localhost:8050/sse"
    }
  }
}
```

> **Note for Windsurf users**: Use `serverUrl` instead of `url` in your configuration:
> ```json
> {
>   "mcpServers": {
>     "sfcore-th-dev": {
>       "transport": "sse",
>       "serverUrl": "http://localhost:8050/sse"
>     }
>   }
> }
> ```

> **Note for n8n users**: Use host.docker.internal instead of localhost since n8n has to reach outside of its own container to the host machine:
> 
> So the full URL in the MCP node would be: http://host.docker.internal:8050/sse

Make sure to update the port if you are using a value other than the default 8050.

### Python with Stdio Configuration

Add this server to your MCP configuration for Claude Desktop, Windsurf, or any other MCP client:

```json
{
  "mcpServers": {
    "sfcore-th-dev": {
      "command": "your/path/to/sfcore-th-dev/.venv/Scripts/python.exe",
      "args": ["your/path/to/sfcore-th-dev/src/main.py"],
      "env": {
        "TRANSPORT": "stdio"
      }
    }
  }
}
```

### Docker with Stdio Configuration

```json
{
  "mcpServers": {
    "sfcore-th-dev": {
      "command": "docker",
      "args": ["run", "--rm", "-i", 
               "-e", "TRANSPORT", 
               "ghcr.io/jorgesolebur/mcp-sfcore-th-dev:latest"],
      "env": {
        "TRANSPORT": "stdio"
      }
    }
  }
}
```

## Extending the Server

This template provides a foundation for building more comprehensive CCI integrations. To add new CCI tools:

1. Create a new `@mcp.tool()` method
2. Use the `get_cci_command_instructions()` utility function for consistent behavior
3. Example:
   ```python
   @mcp.tool()
   async def deploy_to_org(org_name: str = "dev") -> str:
       command = f"cci flow run deploy --org {org_name}"
       purpose = f"Deploy to org '{org_name}'"
       return get_cci_command_instructions(command, purpose)
   ```

This ensures all tools have consistent command execution and error handling.

## Available Tools

### Environment Setup
- **`check_cci_installation`**: Checks if CumulusCI is installed and provides installation/upgrade instructions

### Scratch Org Management
- **`create_dev_scratch_org`**: Creates a development scratch org using `cci flow run dev_org --org <org_name>`
- **`create_feature_scratch_org`**: Creates a feature/QA scratch org using `cci flow run ci_feature_2gp --org <org_name>`
- **`create_beta_scratch_org`**: Creates a beta/regression scratch org using `cci flow run regression_org --org <org_name>`
- **`list_orgs`**: Lists all connected CumulusCI orgs using `cci org list`
- **`open_org`**: Opens the specified org in a browser using `cci org browser --org <org_name>`

### Development Operations
- **`run_tests`**: Runs Apex tests in a specified org using `cci task run run_all_tests_locally --org <org_name>`
- **`retrieve_changes`**: Retrieves metadata changes from the specified org using `cci task run retrieve_changes --org <org_name>`
- **`deploy`**: Deploys local metadata to the specified org using `cci task run deploy --org <org_name>`

### Generic CCI Task Handler
- **`run_generic_cci_task`**: Handles any CCI task that doesn't have a dedicated tool following a 3-step approach:
  1. Checks if the task exists using `cci task list`
  2. Gets task information and parameters using `cci task info` or `cci task run --help`
  3. Runs the task with appropriate parameters after collecting required values from the user

All CCI tools provide setup guidance if needed and follow consistent error handling patterns.

## MCP Resources

The server provides framework-specific documentation through MCP resources. These resources give agents contextual information about development practices and standards.

### Available Resources

Access resources using the URI pattern: `framework://<framework-name>`

- **`framework://salesforce-triggers`**: Comprehensive guidelines for developing Apex triggers
  - Trigger framework architecture
  - Handler pattern implementation
  - Best practices and anti-patterns
  - Testing strategies
  - Performance considerations

- **`framework://salesforce-logging`**: Logging standards and best practices
  - Custom logger implementation
  - Log levels and usage guidelines
  - Performance considerations
  - Production logging strategies
  - Security and privacy considerations

- **`framework://salesforce-cache-manager`**: Platform Cache management framework for performance optimization
  - Three cache types: Organization, Session, and Transaction
  - Declarative configuration with custom metadata
  - Usage examples and best practices
  - Performance monitoring and debugging
  - Security considerations for cached data

### Using Resources

Agents can request framework documentation when needed:

```json
{
  "method": "resources/read",
  "params": {
    "uri": "framework://salesforce-triggers"
  }
}
```

This provides on-demand access to framework-specific guidance without cluttering tool descriptions.

## Future Enhancements

Consider adding:
- Additional framework resources (LWC, Aura, Flows)
- More CCI operation tools
- Integration with CI/CD pipelines
- Advanced testing workflows
