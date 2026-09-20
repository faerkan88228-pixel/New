"""
LLM Providers Integration
Connects to OpenAI, Anthropic, DeepSeek, Google, Ollama, and local vLLM.
"""

import json
from typing import Any, AsyncGenerator, Dict, List, Optional
import httpx
from app.config import settings


class BaseLLMClient:
    async def chat_completion(
        self,
        messages: List[Dict[str, Any]],
        model: str,
        temperature: float = 0.7,
        tools: Optional[List[Dict[str, Any]]] = None
    ) -> Dict[str, Any]:
        raise NotImplementedError


class OpenAICompatibleClient(BaseLLMClient):
    """Client for OpenAI, DeepSeek, Groq, OpenRouter, and vLLM."""

    def __init__(self, base_url: str, api_key: str):
        self.base_url = base_url.rstrip("/")
        self.api_key = api_key

    async def chat_completion(
        self,
        messages: List[Dict[str, Any]],
        model: str,
        temperature: float = 0.7,
        tools: Optional[List[Dict[str, Any]]] = None
    ) -> Dict[str, Any]:
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        payload: Dict[str, Any] = {
            "model": model,
            "messages": messages,
            "temperature": temperature,
        }
        if tools:
            payload["tools"] = tools
            payload["tool_choice"] = "auto"

        async with httpx.AsyncClient(timeout=60.0) as client:
            resp = await client.post(f"{self.base_url}/chat/completions", headers=headers, json=payload)
            resp.raise_for_status()
            data = resp.json()
            choice = data["choices"][0]["message"]
            return {
                "content": choice.get("content") or "",
                "tool_calls": choice.get("tool_calls"),
                "usage": data.get("usage", {})
            }


class OllamaClient(BaseLLMClient):
    """Client for locally running Ollama instance."""

    def __init__(self, base_url: str = "http://localhost:11434"):
        self.base_url = base_url.rstrip("/")

    async def chat_completion(
        self,
        messages: List[Dict[str, Any]],
        model: str = "qwen2.5:latest",
        temperature: float = 0.7,
        tools: Optional[List[Dict[str, Any]]] = None
    ) -> Dict[str, Any]:
        payload = {
            "model": model,
            "messages": messages,
            "stream": False,
            "options": {"temperature": temperature}
        }
        async with httpx.AsyncClient(timeout=60.0) as client:
            resp = await client.post(f"{self.base_url}/api/chat", json=payload)
            resp.raise_for_status()
            data = resp.json()
            return {
                "content": data.get("message", {}).get("content", ""),
                "tool_calls": None,
                "usage": {"total_tokens": data.get("eval_count", 0)}
            }
