"""
Model Catalog & Capabilities Registry
Unified catalog of supported LLMs across Zero-Token and API providers.
"""

from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class ModelInfo(BaseModel):
    id: str
    name: str
    provider: str
    category: str  # "reasoning", "general", "coding", "fast"
    context_window: int
    zero_token_supported: bool = True
    supports_tools: bool = True
    supports_vision: bool = False
    description: str


AVAILABLE_MODELS: Dict[str, ModelInfo] = {
    # Qwen Family (Flagship)
    "qwen-2.5-72b": ModelInfo(
        id="qwen-2.5-72b",
        name="Qwen 2.5 72B Instruct",
        provider="Qwen / Alibaba",
        category="general",
        context_window=131072,
        zero_token_supported=True,
        supports_tools=True,
        description="Top-tier open-weights model by Alibaba, stellar reasoning, multilingual, and tool execution."
    ),
    "qwen-2.5-coder-32b": ModelInfo(
        id="qwen-2.5-coder-32b",
        name="Qwen 2.5 Coder 32B",
        provider="Qwen / Alibaba",
        category="coding",
        context_window=131072,
        zero_token_supported=True,
        supports_tools=True,
        description="State of the art open coding model, expert at refactoring, debugging, and terminal automation."
    ),
    "qwen-max": ModelInfo(
        id="qwen-max",
        name="Qwen-Max (Tongyi Qianwen)",
        provider="Qwen / Alibaba",
        category="reasoning",
        context_window=32768,
        zero_token_supported=True,
        supports_tools=True,
        description="Alibaba's largest proprietary model with deep chain of thought."
    ),

    # DeepSeek Family
    "deepseek-r1": ModelInfo(
        id="deepseek-r1",
        name="DeepSeek R1 (Reasoning)",
        provider="DeepSeek",
        category="reasoning",
        context_window=65536,
        zero_token_supported=True,
        supports_tools=True,
        description="Frontier reasoning model with transparent chain-of-thought tokens."
    ),
    "deepseek-v3": ModelInfo(
        id="deepseek-v3",
        name="DeepSeek V3",
        provider="DeepSeek",
        category="general",
        context_window=65536,
        zero_token_supported=True,
        supports_tools=True,
        description="671B MoE architecture with ultra-fast generation and high accuracy."
    ),

    # Claude / Anthropic
    "claude-3-5-sonnet": ModelInfo(
        id="claude-3-5-sonnet",
        name="Claude 3.5 Sonnet",
        provider="Anthropic",
        category="general",
        context_window=200000,
        zero_token_supported=True,
        supports_tools=True,
        supports_vision=True,
        description="Industry gold standard for code generation, agentic reasoning, and computer use."
    ),

    # OpenAI
    "gpt-4o": ModelInfo(
        id="gpt-4o",
        name="GPT-4o Omnimodal",
        provider="OpenAI",
        category="general",
        context_window=128000,
        zero_token_supported=True,
        supports_tools=True,
        supports_vision=True,
        description="Omni multimodal flagship with native tool calling."
    ),
    "o3-mini": ModelInfo(
        id="o3-mini",
        name="o3-mini Reasoning",
        provider="OpenAI",
        category="reasoning",
        context_window=200000,
        zero_token_supported=True,
        supports_tools=True,
        description="Fast STEM and coding reasoning model."
    ),

    # Google Gemini
    "gemini-2.0-flash": ModelInfo(
        id="gemini-2.0-flash",
        name="Gemini 2.0 Flash",
        provider="Google",
        category="fast",
        context_window=1048576,
        zero_token_supported=True,
        supports_tools=True,
        description="Sub-second latency with 1M token context window."
    ),

    # Moonshot Kimi
    "kimi-k1.5": ModelInfo(
        id="kimi-k1.5",
        name="Kimi k1.5 Long-Context",
        provider="Moonshot AI",
        category="general",
        context_window=200000,
        zero_token_supported=True,
        supports_tools=True,
        description="Chinese & English long context reasoning and document analysis."
    ),

    # Local / Self-Hosted
    "ollama-local": ModelInfo(
        id="ollama-local",
        name="Ollama Local Instance",
        provider="Ollama",
        category="general",
        context_window=32768,
        zero_token_supported=True,
        supports_tools=True,
        description="Locally hosted models via http://localhost:11434 with zero cloud dependencies."
    )
}
