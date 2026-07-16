#!/usr/bin/env python3
"""HEAL AI Research Assistant — FastAPI + Claude backend."""

import json
from pathlib import Path

import anthropic
import httpx
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, StreamingResponse
from pydantic import BaseModel

HEAL_BASE = "https://heal-dev.apps.renci.org/search-api"
PROJECT_ROOT = Path(__file__).parent.parent
aclient = anthropic.AsyncAnthropic()  # reads ANTHROPIC_API_KEY from env

SYSTEM_PROMPT = """You are an AI research assistant for the HEAL (Helping to End Addiction Long-term) \
Data Platform — a NIH initiative funding research on pain management and opioid use disorder.

You help researchers discover relevant data across HEAL studies. You have four search tools:
- search_concepts: Find biomedical concepts (diseases, phenotypes, biological processes, etc.)
- search_variables: Find data variables/measures collected across studies
- search_studies: Find research studies in the HEAL program
- search_cdes: Find Common Data Elements (CDEs) or Case Report Forms used across studies

When a user asks a question:
1. Use the appropriate tool(s) to search for relevant information
2. Synthesize results into a clear, well-organized answer
3. Mention key details: names, types, descriptions, and counts
4. Limit lists to the 5–7 most relevant items
5. Use plain language appropriate for biomedical researchers

If a question spans multiple categories (e.g., "what concepts and studies relate to chronic pain"), \
search both and combine the findings."""

TOOLS = [
    {
        "name": "search_concepts",
        "description": (
            "Search for biomedical concepts related to a topic in the HEAL data platform. "
            "Returns concepts like diseases, phenotypes, biological processes, and anatomical structures. "
            "Use this when the user asks about conditions, disorders, or general biomedical topics."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "query": {"type": "string", "description": "The search term or phrase"},
                "size": {"type": "integer", "description": "Number of results to return (default 10)", "default": 10},
            },
            "required": ["query"],
        },
    },
    {
        "name": "search_variables",
        "description": (
            "Search for data variables or measures collected in HEAL studies. "
            "Use this when the user asks what data was collected, measured, or recorded — "
            "e.g., pain scales, opioid dosage, biomarkers, questionnaire items."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "query": {"type": "string", "description": "The search term or phrase"},
                "size": {"type": "integer", "description": "Number of results to return (default 10)", "default": 10},
            },
            "required": ["query"],
        },
    },
    {
        "name": "search_studies",
        "description": (
            "Search for research studies in the HEAL data platform. "
            "Use this when the user asks about specific studies, trial designs, or research programs."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "query": {"type": "string", "description": "The search term or phrase"},
                "size": {"type": "integer", "description": "Number of results to return (default 10)", "default": 10},
            },
            "required": ["query"],
        },
    },
    {
        "name": "search_cdes",
        "description": (
            "Search for Common Data Elements (CDEs) or Case Report Forms (CRFs) used across HEAL studies. "
            "Use this when the user asks about standardized instruments, forms, or cross-study measures."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "query": {"type": "string", "description": "The search term or phrase"},
                "size": {"type": "integer", "description": "Number of results to return (default 10)", "default": 10},
            },
            "required": ["query"],
        },
    },
]


def _normalize_concepts(raw: dict) -> dict:
    """
    /search returns:
      result[0] = {"hits": {"hits": [<ES docs>]}}
      result[1] = <total int>
      result[2] = {"phenotypic feature": N, "disease": N, ...}
    """
    result = raw.get("result", [])
    if not result or not isinstance(result[0], dict):
        return {"total": 0, "concepts": []}

    hits_raw = result[0].get("hits", {}).get("hits", [])
    total = result[1] if len(result) > 1 and isinstance(result[1], int) else len(hits_raw)
    type_breakdown = result[2] if len(result) > 2 and isinstance(result[2], dict) else {}

    concepts = []
    for hit in hits_raw:
        src = hit.get("_source", {})
        concepts.append(
            {
                "id": hit.get("_id"),
                "score": round(hit.get("_score", 0), 3),
                "name": src.get("name"),
                "description": src.get("description"),
                "type": src.get("concept_type") or src.get("type"),
                "synonyms": src.get("search_terms", [])[:5],
                "programs": src.get("programs", []),
            }
        )

    return {"total": total, "type_breakdown": type_breakdown, "concepts": concepts}


def _result_count(result: dict) -> int | None:
    if not isinstance(result, dict):
        return None
    for key in ("total", "total_items", "total_results"):
        if key in result and isinstance(result[key], int):
            return result[key]
    for key in ("concepts", "elements", "studies", "variables", "cdes", "results", "hits"):
        if key in result and isinstance(result[key], list):
            return len(result[key])
    for v in result.values():
        if isinstance(v, list):
            return len(v)
    return None


async def call_heal_tool(name: str, inputs: dict) -> dict:
    query = inputs["query"]
    size = inputs.get("size", 10)

    async with httpx.AsyncClient(timeout=30.0) as client:
        if name == "search_concepts":
            r = await client.post(f"{HEAL_BASE}/search", json={"query": query, "size": size})
            r.raise_for_status()
            return _normalize_concepts(r.json())

        endpoint_map = {
            "search_variables": "/variables",
            "search_studies": "/studies",
            "search_cdes": "/cdes",
        }
        r = await client.post(f"{HEAL_BASE}{endpoint_map[name]}", json={"query": query, "size": size})
        r.raise_for_status()
        return r.json()


# ── FastAPI app ──────────────────────────────────────────────────────────────

app = FastAPI(title="HEAL AI Research Assistant")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


class ChatRequest(BaseModel):
    message: str
    history: list[dict] = []  # [{role, content}] — plain text only


@app.get("/")
async def index():
    return FileResponse(PROJECT_ROOT / "chat_ui.html")


@app.post("/chat")
async def chat(req: ChatRequest):
    async def generate():
        messages = list(req.history) + [{"role": "user", "content": req.message}]

        try:
            for _ in range(10):  # guard against runaway loops
                async with aclient.messages.stream(
                    model="claude-opus-4-6",
                    max_tokens=8192,
                    system=SYSTEM_PROMPT,
                    tools=TOOLS,
                    messages=messages,
                ) as stream:
                    async for event in stream:
                        if event.type == "content_block_start":
                            if (
                                hasattr(event, "content_block")
                                and event.content_block.type == "tool_use"
                            ):
                                yield (
                                    f"data: {json.dumps({'type': 'tool_start', 'name': event.content_block.name})}\n\n"
                                )
                        elif event.type == "content_block_delta":
                            if hasattr(event, "delta") and event.delta.type == "text_delta":
                                yield (
                                    f"data: {json.dumps({'type': 'text', 'content': event.delta.text})}\n\n"
                                )

                    final = await stream.get_final_message()

                if final.stop_reason == "tool_use":
                    tool_results = []
                    for block in final.content:
                        if block.type == "tool_use":
                            try:
                                result = await call_heal_tool(block.name, block.input)
                                count = _result_count(result)
                                yield (
                                    f"data: {json.dumps({'type': 'tool_done', 'name': block.name, 'count': count})}\n\n"
                                )
                            except Exception as exc:
                                result = {"error": str(exc)}
                                yield (
                                    f"data: {json.dumps({'type': 'tool_error', 'name': block.name, 'error': str(exc)})}\n\n"
                                )

                            tool_results.append(
                                {
                                    "type": "tool_result",
                                    "tool_use_id": block.id,
                                    "content": json.dumps(result),
                                }
                            )

                    messages.append({"role": "assistant", "content": final.content})
                    messages.append({"role": "user", "content": tool_results})
                else:
                    break

            yield f"data: {json.dumps({'type': 'done'})}\n\n"

        except Exception as exc:
            yield f"data: {json.dumps({'type': 'error', 'message': str(exc)})}\n\n"

    return StreamingResponse(
        generate(),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8081)
