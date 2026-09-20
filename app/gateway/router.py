"""
Model Router & Fallback Dispatcher
Routes requests to API keys or Zero-Token web bridges with auto-failover.
"""

import time
from typing import Any, AsyncGenerator, Dict, List, Optional
from app.config import settings
from app.gateway.catalog import AVAILABLE_MODELS
from app.gateway.providers import OpenAICompatibleClient, OllamaClient
from app.gateway.zero_token import zero_token_gateway


class ModelRouter:
    """Intelligent Model Router with provider failover."""

    def __init__(self):
        self._provider_clients: Dict[str, Any] = {}
        self._init_clients()

    def _init_clients(self):
        if settings.llm.openai_api_key:
            self._provider_clients["openai"] = OpenAICompatibleClient(
                "https://api.openai.com/v1", settings.llm.openai_api_key
            )
        if settings.llm.deepseek_api_key:
            self._provider_clients["deepseek"] = OpenAICompatibleClient(
                "https://api.deepseek.com/v1", settings.llm.deepseek_api_key
            )
        if settings.llm.groq_api_key:
            self._provider_clients["groq"] = OpenAICompatibleClient(
                "https://api.groq.com/openai/v1", settings.llm.groq_api_key
            )
        if settings.llm.openrouter_api_key:
            self._provider_clients["openrouter"] = OpenAICompatibleClient(
                "https://openrouter.ai/api/v1", settings.llm.openrouter_api_key
            )
        # Ollama local client
        self._provider_clients["ollama"] = OllamaClient(settings.llm.ollama_url)

    async def complete(
        self,
        messages: List[Dict[str, Any]],
        model_id: str = "qwen-2.5-72b",
        temperature: float = 0.7,
        tools: Optional[List[Dict[str, Any]]] = None
    ) -> Dict[str, Any]:
        """Execute chat completion with automatic fallback."""
        start_time = time.time()

        # Check if direct provider is configured
        if "deepseek" in model_id and "deepseek" in self._provider_clients:
            try:
                res = await self._provider_clients["deepseek"].chat_completion(messages, model_id, temperature, tools)
                res["provider_used"] = "deepseek-api"
                res["latency_ms"] = int((time.time() - start_time) * 1000)
                return res
            except Exception:
                pass

        if "gpt" in model_id and "openai" in self._provider_clients:
            try:
                res = await self._provider_clients["openai"].chat_completion(messages, model_id, temperature, tools)
                res["provider_used"] = "openai-api"
                res["latency_ms"] = int((time.time() - start_time) * 1000)
                return res
            except Exception:
                pass

        # Zero-Token Gateway execution (default / fallback)
        chunks = []
        async for chunk in zero_token_gateway.stream_response("qwen", messages, tools):
            chunks.append(chunk)

        content = "".join(chunks).strip()
        return {
            "content": content,
            "tool_calls": None,
            "provider_used": "openclaw-zero-token",
            "model": model_id,
            "latency_ms": int((time.time() - start_time) * 1000)
        }


model_router = ModelRouter()
