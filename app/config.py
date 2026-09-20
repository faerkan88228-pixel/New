"""
OmniNexus Studio Configuration
Central settings management for Agent, Model Gateway, Qwen3-TTS, and Android Bridge.
"""

import os
from pathlib import Path
from pydantic import BaseModel, Field

BASE_DIR = Path(__file__).resolve().parent.parent
WORKSPACE_DIR = BASE_DIR / "data" / "workspace"
AUDIOBOOKS_DIR = BASE_DIR / "data" / "audiobooks"
SAMPLES_DIR = BASE_DIR / "data" / "samples"

# Ensure runtime directories exist
WORKSPACE_DIR.mkdir(parents=True, exist_ok=True)
AUDIOBOOKS_DIR.mkdir(parents=True, exist_ok=True)
SAMPLES_DIR.mkdir(parents=True, exist_ok=True)


class ServerConfig(BaseModel):
    host: str = "0.0.0.0"
    port: int = 8000
    debug: bool = False
    app_name: str = "OmniNexus Studio"
    version: str = "2.0.0"


class LLMConfig(BaseModel):
    default_provider: str = Field(default=os.getenv("DEFAULT_PROVIDER", "zero-token"))
    default_model: str = Field(default=os.getenv("DEFAULT_MODEL", "qwen-2.5-72b"))
    temperature: float = 0.7
    max_tokens: int = 4096
    
    # API Keys (optional if using zero-token or local Ollama)
    openai_api_key: str = Field(default=os.getenv("OPENAI_API_KEY", ""))
    anthropic_api_key: str = Field(default=os.getenv("ANTHROPIC_API_KEY", ""))
    deepseek_api_key: str = Field(default=os.getenv("DEEPSEEK_API_KEY", ""))
    gemini_api_key: str = Field(default=os.getenv("GEMINI_API_KEY", ""))
    groq_api_key: str = Field(default=os.getenv("GROQ_API_KEY", ""))
    openrouter_api_key: str = Field(default=os.getenv("OPENROUTER_API_KEY", ""))
    
    # Local endpoints
    ollama_url: str = Field(default=os.getenv("OLLAMA_URL", "http://localhost:11434"))
    vllm_url: str = Field(default=os.getenv("VLLM_URL", "http://localhost:8001"))
    zero_token_enabled: bool = True


class TTSConfig(BaseModel):
    engine_backend: str = "hybrid"  # "hybrid" | "qwentts_cpp" | "api" | "python"
    sample_rate: int = 24000
    default_speaker: str = "Ryan"
    default_language: str = "English"
    audio_format: str = "wav"
    qwen_api_url: str = Field(default=os.getenv("QWEN_API_URL", "http://127.0.0.1:7860"))
    qwentts_bin_path: str = str(BASE_DIR / "native" / "qwentts" / "qwen-tts")
    max_chunk_chars: int = 280
    enable_caching: bool = True


class AndroidConfig(BaseModel):
    adb_host: str = "127.0.0.1"
    adb_port: int = 5037
    virtual_device_enabled: bool = True
    default_device_id: str = "emulator-5554"
    screen_width: int = 1080
    screen_height: int = 2400


class AppSettings(BaseModel):
    server: ServerConfig = Field(default_factory=ServerConfig)
    llm: LLMConfig = Field(default_factory=LLMConfig)
    tts: TTSConfig = Field(default_factory=TTSConfig)
    android: AndroidConfig = Field(default_factory=AndroidConfig)
    workspace_dir: Path = WORKSPACE_DIR
    audiobooks_dir: Path = AUDIOBOOKS_DIR
    samples_dir: Path = SAMPLES_DIR


settings = AppSettings()
