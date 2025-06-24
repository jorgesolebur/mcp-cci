<h1 align="center">MCP-CCI: CumulusCI Integration for AI Agents</h1>

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
- CumulusCI installed and configured
- Access to a Salesforce org (Dev Hub for scratch orgs)
- Docker if running the MCP server as a container (recommended)

## Installation

### Using uv

1. Install uv if you don't have it:
   ```bash
   pip install uv
   ```

2. Clone this repository:
   ```bash
   git clone <your-repo-url>
   cd mcp-cci
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
   docker build -t mcp/cci --build-arg PORT=8050 .
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
docker run -p 8050:8050 mcp/cci
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
    "cci": {
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
>     "cci": {
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
    "cci": {
      "command": "your/path/to/mcp-cci/.venv/Scripts/python.exe",
      "args": ["your/path/to/mcp-cci/src/main.py"],
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
    "cci": {
      "command": "docker",
      "args": ["run", "--rm", "-i", 
               "-e", "TRANSPORT", 
               "mcp/cci"],
      "env": {
        "TRANSPORT": "stdio"
      }
    }
  }
}
```

## Extending the Server

This template provides a foundation for building more comprehensive CCI integrations. To extend:

1. Add more CCI tools by creating methods with the `@mcp.tool()` decorator
2. Modify the `utils.py` file to add more CCI command wrappers
3. Consider adding prompts and resources with `@mcp.resource()` and `@mcp.prompt()`

## Available Tools

- **`create_scratch_org`**: Creates a new scratch org using `cci flow run dev_org --org <org_name>`

## Future Enhancements

Consider adding tools for:
- Deploying to orgs
- Running tests
- Managing org configurations
- Viewing org information
- Data operations
