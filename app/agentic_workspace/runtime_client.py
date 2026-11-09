"""Server-side client for the isolated original OpenManus runtime."""
from __future__ import annotations

import os
from typing import Any
from urllib.parse import urlparse

import httpx
from fastapi import HTTPException


def runtime_endpoint() -> tuple[str, str]:
    base = os.getenv("OPENMANUS_RUNTIME_URL", "").rstrip("/")
    token = os.getenv("OPENMANUS_RUNTIME_TOKEN", "")
    try:
        parsed = urlparse(base)
        valid = (
            parsed.scheme == "https"
            and bool(parsed.hostname)
            and parsed.port in {None, 443}
            and parsed.path in {"", "/"}
            and not parsed.query
            and not parsed.fragment
            and not parsed.username
            and not parsed.password
            and not parsed.username
            and not parsed.password
        )
    except ValueError:
        valid = False
    if not valid or not token:
        raise HTTPException(
            status_code=503,
            detail="OpenManus runtime is not configured with an HTTPS endpoint and server token.",
        )
    return base + "/v1/agent/run", token


def build_runtime_payload(goal: str, contexts: list[dict[str, Any]]) -> dict[str, Any]:
    return {
        "goal": goal,
        "timeout_seconds": 240,
        "skill_contexts": [
            {
                "kind": item["kind"],
                "name": item["name"],
                "source_url": item["source_url"],
                "source_sha": item["source_sha"],
                "content": item["content"],
            }
            for item in contexts[:8]
        ],
    }


async def run_openmanus_runtime(goal: str, contexts: list[dict[str, Any]]) -> dict[str, Any]:
    endpoint, token = runtime_endpoint()
    payload = build_runtime_payload(goal, contexts)
    try:
        async with httpx.AsyncClient(
            timeout=httpx.Timeout(260.0, connect=15.0),
            follow_redirects=False,
        ) as client:
            response = await client.post(
                endpoint,
                headers={"X-Prometheus-Runtime-Token": token},
                json=payload,
            )
    except httpx.HTTPError as exc:
        raise HTTPException(
            status_code=503,
            detail=f"OpenManus runtime is unreachable ({type(exc).__name__}).",
        ) from exc

    if response.status_code == 401:
        raise HTTPException(status_code=503, detail="OpenManus runtime authentication failed.")
    if response.status_code >= 400:
        raise HTTPException(
            status_code=502,
            detail=f"OpenManus runtime returned HTTP {response.status_code}.",
        )
    try:
        result = response.json()
    except ValueError as exc:
        raise HTTPException(status_code=502, detail="OpenManus runtime returned invalid JSON.") from exc
    if result.get("runtime") != "openmanus" or result.get("status") != "completed":
        raise HTTPException(status_code=502, detail="Response did not confirm successful OpenManus execution.")
    return result
