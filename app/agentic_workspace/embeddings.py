"""Gemini text embedding client used by the Agentic Workspace vector retriever."""
from __future__ import annotations

import math
import os
from typing import Literal

import httpx
from fastapi import HTTPException

EMBEDDING_MODEL = "gemini-embedding-001"
EMBEDDING_DIMENSIONS = 768
EMBEDDING_ENDPOINT = (
    "https://generativelanguage.googleapis.com/v1beta/models/"
    + EMBEDDING_MODEL
    + ":embedContent"
)
ALLOWED_TASK_TYPES = {"RETRIEVAL_DOCUMENT", "RETRIEVAL_QUERY"}


class GeminiEmbeddingProvider:
    def __init__(
        self,
        api_key: str | None = None,
        transport: httpx.AsyncBaseTransport | None = None,
    ) -> None:
        self.api_key = (api_key if api_key is not None else os.getenv("GEMINI_API_KEY", "")).strip()
        self.transport = transport

    @property
    def configured(self) -> bool:
        return bool(self.api_key)

    async def embed_text(
        self,
        text: str,
        task_type: Literal["RETRIEVAL_DOCUMENT", "RETRIEVAL_QUERY"],
    ) -> list[float]:
        if not self.configured:
            raise HTTPException(
                status_code=503,
                detail="GEMINI_API_KEY is not configured; vector retrieval is unavailable.",
            )
        if task_type not in ALLOWED_TASK_TYPES:
            raise HTTPException(status_code=422, detail="Unsupported Gemini embedding task type.")
        if not text or not text.strip() or len(text) > 3_000:
            raise HTTPException(status_code=422, detail="Embedding text is empty or exceeds 3,000 characters.")

        try:
            async with httpx.AsyncClient(
                timeout=30.0,
                follow_redirects=False,
                transport=self.transport,
            ) as client:
                response = await client.post(
                    EMBEDDING_ENDPOINT,
                    headers={
                        "x-goog-api-key": self.api_key,
                        "Content-Type": "application/json",
                    },
                    json={
                        "taskType": task_type,
                        "outputDimensionality": EMBEDDING_DIMENSIONS,
                        "content": {"parts": [{"text": text}]},
                    },
                )
        except httpx.HTTPError as exc:
            raise HTTPException(
                status_code=503,
                detail=f"Gemini embedding service is unreachable ({type(exc).__name__}).",
            ) from exc

        if response.status_code >= 400:
            raise HTTPException(
                status_code=502,
                detail=f"Gemini embedding service returned HTTP {response.status_code}.",
            )
        try:
            values = response.json()["embedding"]["values"]
            vector = [float(value) for value in values]
        except (KeyError, TypeError, ValueError) as exc:
            raise HTTPException(
                status_code=502,
                detail="Gemini embedding service returned an invalid vector.",
            ) from exc

        if len(vector) != EMBEDDING_DIMENSIONS or not all(math.isfinite(value) for value in vector):
            raise HTTPException(
                status_code=502,
                detail=f"Gemini embedding must contain {EMBEDDING_DIMENSIONS} finite values.",
            )
        return vector
