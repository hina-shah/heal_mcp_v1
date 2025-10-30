# heal_mcp_v1

MCP server for HEAL V1

## HEAL MCP server (FastMCP + OpenAPI)

This repository contains a minimal MCP server scaffold that uses FastMCP's
OpenAPI integration to expose the HEAL Search API (OpenAPI at
`https://heal.renci.org/search-api/openapi.json`) as an MCP server.

Quick start:

1. Create and activate a Python 3.10+ virtualenv.
2. Install deps:

```bash
pip install -r requirements.txt
```

3. Run the server locally (HTTP transport on port 8080):

```bash
python -m src.heal_mcp_server
```

The server will expose MCP endpoints generated from the HEAL OpenAPI
spec. See `.github/copilot-instructions.md` for agent-focused tips.
