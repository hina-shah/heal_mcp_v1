# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Overview

This is an MCP (Model Context Protocol) server that exposes the HEAL Search API via FastMCP's OpenAPI integration. The server dynamically generates MCP endpoints from the HEAL OpenAPI specification at `https://heal.renci.org/search-api/openapi.json`.

## Development Commands

### Setup
```bash
# Create and activate Python 3.10+ virtual environment
pip install -r requirements.txt
```

### Running the Server

**Quick Start (recommended):**
```bash
# Use the convenience script
./run_server.sh
```

**Manual Start:**
```bash
# Run with HTTP transport on port 8080
python -m src.heal_mcp_server
```

The server runs on `http://0.0.0.0:8080/mcp` by default, allowing external connections (e.g., from host machine when running in a container).

**Alternative: STDIO Transport**
To use STDIO transport (for local development or Claude Desktop with stdio config):
```python
# In src/heal_mcp_server.py, change:
mcp.run()  # Uses STDIO by default
```

### Testing
```bash
# Run tests with pytest
pytest tests/
```

### Testing with MCP Inspector

**Install and run MCP Inspector:**
```bash
npx @modelcontextprotocol/inspector
```

**Connect to the server:**
- If running locally: `http://localhost:8080/mcp`
- If running in a devcontainer with port forwarding: `http://localhost:8080/mcp`

The Inspector will show all 9 tools generated from the HEAL OpenAPI spec and let you test them interactively.

### Using with Claude Desktop

Add to your Claude Desktop configuration file:

**Config file locations:**
- macOS: `~/Library/Application Support/Claude/claude_desktop_config.json`
- Windows: `%APPDATA%\Claude\claude_desktop_config.json`
- Linux: `~/.config/Claude/claude_desktop_config.json`

**Configuration:**
```json
{
  "mcpServers": {
    "heal-search-mcp": {
      "url": "http://localhost:8080/mcp"
    }
  }
}
```

Note: Adjust the URL if accessing from a different host. Restart Claude Desktop after updating the config.

## Architecture

### Core Components

**src/heal_mcp_server.py** - Main server implementation
- `create_mcp()`: Factory function that creates the MCP server instance
  - Fetches the HEAL OpenAPI spec from the remote endpoint
  - Uses `FastMCP.from_openapi()` to dynamically generate MCP tools/resources from the spec
  - Returns a configured FastMCP instance
- Uses `httpx.AsyncClient` with base URL `https://heal.renci.org/search-api`
- Server is named "heal-search-mcp"

### Key Dependencies
- **fastmcp** (>=2.13.0): Framework for creating MCP servers with OpenAPI support
- **httpx** (>=0.24.0): Async HTTP client for fetching OpenAPI spec and proxying API calls
- **mcp**: Core MCP protocol implementation

### Design Pattern

This server uses a **thin proxy pattern** - it doesn't implement API endpoints directly. Instead, it:
1. Fetches the OpenAPI specification at runtime
2. Delegates to FastMCP to auto-generate MCP tools based on the spec
3. Relies on the httpx client to proxy requests to the actual HEAL API

The code intentionally has commented-out async/sync variants showing evolution of the implementation. The current working pattern uses `asyncio.run()` within `create_mcp()` to handle async client initialization synchronously, letting FastMCP manage the async runtime.
