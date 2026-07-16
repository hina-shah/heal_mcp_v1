#!/usr/bin/env python3

import logging
import httpx
from fastmcp import FastMCP
import asyncio

OPENAPI_URL = "https://heal-dev.apps.renci.org/search-api/openapi.json"
BASE_URL    = "https://heal-dev.apps.renci.org/search-api"

async def create_mcp():
    client = httpx.AsyncClient(base_url=BASE_URL, timeout=30.0)
    response = await client.get(OPENAPI_URL)
    response.raise_for_status()
    spec_json = response.json()

    mcp = FastMCP.from_openapi(
        openapi_spec=spec_json,
        client=client,
        name="heal-search-mcp",
    )
    return mcp, client

async def main():
    logging.basicConfig(level=logging.INFO)
    mcp, client = await create_mcp()
    try:
        await mcp.run_async(transport="streamable-http", host="0.0.0.0", port=8080, path="/mcp")
    finally:
        await client.aclose()

if __name__ == "__main__":
    asyncio.run(main())

# """Minimal FastMCP server that exposes the HEAL Search API via OpenAPI.

# This file uses FastMCP's OpenAPI loader to create an MCP server from the
# published HEAL OpenAPI spec at https://heal.renci.org/search-api/openapi.json.

# Run with: python -m src.heal_mcp_server
# Or: fastmcp run src/heal_mcp_server.py
# """
# import logging
# import httpx
# from fastmcp import FastMCP
# import atexit

# OPENAPI_URL = "https://heal.renci.org/search-api/openapi.json"
# BASE_URL    = "https://heal.renci.org/search-api"

# def create_mcp():
#     # Use a synchronous client so we don't bind anything to a closed asyncio loop
#     client = httpx.Client(base_url=BASE_URL, timeout=30.0)
#     atexit.register(client.close)

#     spec = client.get(OPENAPI_URL)
#     spec.raise_for_status()
#     spec_json = spec.json()

#     mcp = FastMCP.from_openapi(
#         openapi_spec=spec_json,
#         client=client,          # safe: sync client, no event-loop coupling
#         name="heal-search-mcp",
#     )
#     return mcp

# if __name__ == "__main__":
#     logging.basicConfig(level=logging.INFO)
#     mcp = create_mcp()
#     mcp.run()  # FastMCP controls asyncio internally

# mcp = create_mcp()
# mcp.run_async()  # Let FastMCP control asyncio itself

# async def create_mcp():
#     # Async HTTP client with base_url
#     client = httpx.AsyncClient(base_url=BASE_URL)

#     # Fetch the OpenAPI spec asynchronously
#     response = await client.get(OPENAPI_URL)
#     response.raise_for_status()
#     spec = response.json()

#     # Create the MCP from the spec
#     mcp = FastMCP.from_openapi(
#         openapi_spec=spec,
#         client=client,
#         name="heal-search-mcp"
#     )
#     return mcp

# async def main():
#     mcp = await create_mcp()
#     mcp.run()   # FastMCP will handle async tools internally

# if __name__ == "__main__":
#     asyncio.run(main())

# def create_mcp():
#     client = httpx.Client(base_url=BASE_URL)
#     response = client.get(OPENAPI_URL)
#     response.raise_for_status()
#     spec = response.json()

#     mcp = FastMCP.from_openapi(
#         openapi_spec=spec,
#         client=client,
#         name="heal-search-mcp"
#     )
#     return mcp
#     # with httpx.Client() as client:
#     #     response = client.get(OPENAPI_URL)
#     #     response.raise_for_status()
#     #     spec = response.json()

#     #     mcp = FastMCP.from_openapi(
#     #         openapi_spec=spec,
#     #         client=client,
#     #         name="heal-search-mcp"
#     #     )
#     #     return mcp

# if __name__ == "__main__":
#     mcp = create_mcp()
#     #mcp.run(transport="http", host="127.0.0.1", port=8080, path="/mcp")
#     mcp.run()

# async def create_mcp():
#     async with httpx.AsyncClient() as client:
#         response = await client.get(OPENAPI_URL)
#         response.raise_for_status()
#         spec = response.json()

#         mcp = FastMCP.from_openapi(
#             openapi_spec=spec,
#             client=client,
#             name="heal-search-mcp"
#         )
#         return mcp

# def create_mcp():
#     """Create a FastMCP instance from the HEAL OpenAPI spec.

#     FastMCP will generate resources/tools/prompts based on the OpenAPI
#     specification. This keeps the server thin and aligned with the API.
#     """
#     api_client = httpx.AsyncClient(base_url="https://heal.renci.org")
#     # fetch the spec (or you can pass the URL)
#     spec = api_client.get("/search-api/openapi.json").json()

#     mcp = FastMCP.from_openapi(client = spec, openapi_spec=OPENAPI_URL, name="heal-search-mcp")
#     return mcp

# async def main():
#     mcp = await create_mcp()
#     mcp.run(transport="http", host="127.0.0.1", port=8080, path="/mcp")

# if __name__ == "__main__":
#     logging.basicConfig(level=logging.INFO)
#     asyncio.run(main())
#     # mcp = create_mcp()
#     # # Default to HTTP transport so web-based clients can connect.
#     # # Path is /mcp so an HTTP client can use e.g. http://127.0.0.1:8080/mcp
#     # mcp.run(transport="http", host="127.0.0.1", port=8080, path="/mcp")
