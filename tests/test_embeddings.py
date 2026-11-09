import unittest

import httpx
from fastapi import HTTPException

from app.agentic_workspace.embeddings import (
    EMBEDDING_DIMENSIONS,
    GeminiEmbeddingProvider,
)


class TestGeminiEmbeddingProvider(unittest.IsolatedAsyncioTestCase):
    async def test_sends_retrieval_document_request_to_gemini(self):
        captured = {}

        def handler(request):
            captured["url"] = str(request.url)
            captured["api_key"] = request.headers.get("x-goog-api-key")
            captured["body"] = request.read().decode("utf-8")
            return httpx.Response(
                200,
                json={"embedding": {"values": [0.25] * EMBEDDING_DIMENSIONS}},
            )

        provider = GeminiEmbeddingProvider(
            api_key="test-key",
            transport=httpx.MockTransport(handler),
        )
        vector = await provider.embed_text(
            "Mobile-first faction interface",
            task_type="RETRIEVAL_DOCUMENT",
        )

        self.assertEqual(len(vector), EMBEDDING_DIMENSIONS)
        self.assertEqual(captured["api_key"], "test-key")
        self.assertIn("gemini-embedding-001:embedContent", captured["url"])
        self.assertIn('"taskType":"RETRIEVAL_DOCUMENT"', captured["body"])
        self.assertIn('"outputDimensionality":768', captured["body"])

    async def test_uses_query_task_type(self):
        captured = {}

        def handler(request):
            captured["body"] = request.read().decode("utf-8")
            return httpx.Response(
                200,
                json={"embedding": {"values": [0.1] * EMBEDDING_DIMENSIONS}},
            )

        provider = GeminiEmbeddingProvider(
            api_key="test-key",
            transport=httpx.MockTransport(handler),
        )
        await provider.embed_text("Build a dashboard", task_type="RETRIEVAL_QUERY")
        self.assertIn('"taskType":"RETRIEVAL_QUERY"', captured["body"])

    async def test_missing_api_key_fails_closed(self):
        provider = GeminiEmbeddingProvider(api_key="", transport=httpx.MockTransport(lambda _: None))
        with self.assertRaises(HTTPException) as error:
            await provider.embed_text("query", task_type="RETRIEVAL_QUERY")
        self.assertEqual(error.exception.status_code, 503)

    async def test_rejects_wrong_embedding_dimension(self):
        provider = GeminiEmbeddingProvider(
            api_key="test-key",
            transport=httpx.MockTransport(
                lambda _: httpx.Response(200, json={"embedding": {"values": [0.1, 0.2]}})
            ),
        )
        with self.assertRaises(HTTPException) as error:
            await provider.embed_text("query", task_type="RETRIEVAL_QUERY")
        self.assertEqual(error.exception.status_code, 502)

    async def test_rejects_unknown_task_type(self):
        provider = GeminiEmbeddingProvider(
            api_key="test-key",
            transport=httpx.MockTransport(lambda _: httpx.Response(200, json={})),
        )
        with self.assertRaises(HTTPException) as error:
            await provider.embed_text("query", task_type="INVALID")
        self.assertEqual(error.exception.status_code, 422)


if __name__ == "__main__":
    unittest.main()
