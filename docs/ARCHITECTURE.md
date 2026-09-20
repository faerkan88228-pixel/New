# OmniNexus Studio Architecture

## Overview
**OmniNexus Studio** is an all-in-one operating platform unifying autonomous multi-agent reasoning, high-fidelity neural speech synthesis, multi-speaker audiobook production, zero-token LLM routing, and Android device automation.

```
                           +--------------------------------------+
                           |          Web Studio UI               |
                           |  (Tailwind + WaveSurfer + Canvas)    |
                           +------------------+-------------------+
                                              | WebSocket / REST
                                              v
                           +--------------------------------------+
                           |           FastAPI Gateway            |
                           |   (CORS, Lifespan, Session Router)   |
                           +------------------+-------------------+
                                              |
        +-----------------------+-------------+-------------+-----------------------+
        |                       |                           |                       |
        v                       v                           v                       v
+----------------+      +---------------+           +---------------+       +---------------+
|  ReAct Agent   |      | Qwen3-TTS &   |           | Android Bridge|       | OpenClaw Model|
|  Orchestrator  |      | Audiobook     |           | & Device      |       | Gateway       |
|                |      | Engine        |           | Commander     |       | (Zero-Token & |
| - OpenManus    |      | - 24kHz Synth |           | - adbutils    |       |  Multi-LLM)   |
| - KODE 3-Chan  |      | - Voice Clone |           | - KernelSU/   |       | - Qwen / Kimi |
| - II-Agent     |      | - Voice Design|           |   Magisk      |       | - Claude/GPT  |
| - Tools (Bash, |      | - WhiskeyCoder|           | - Debloater   |       | - DeepSeek    |
|   Web, FS, REPL)|     |   Audiobook   |           | - 600+ Catalog|       | - Local Ollama|
+----------------+      | - qwentts.cpp |           +---------------+       +---------------+
                        +---------------+
```

---

## 1. Multi-Agent Orchestrator (OpenManus + KODE SDK + II-Agent)
- **Planning Engine**: OpenManus ReAct loop analyzes high-level user tasks, creates structured `ExecutionPlan` steps, and invokes tools dynamically.
- **Three-Channel Event Bus (from KODE Agent SDK)**:
  - `ProgressChannel`: Real-time task step updates, partial reasoning, and tool execution status.
  - `ControlChannel`: Flow control signals (pause, resume, cancel, human-in-the-loop approvals).
  - `MonitorChannel`: Telemetry, execution latency, token accounting, and error logging.
- **Persistent Memory (from II-Agent)**: Multi-turn session state management, chat history retention, and workspace sandbox.

---

## 2. Qwen3-TTS & Audiobook Studio
- **Acoustic Waveform Synthesizer**: Produces true 24,000 Hz / 16-bit PCM WAV audio with phonetic modulation, glottal harmonics, and formant frequency modeling (F1, F2, F3).
- **9 Predefined Speakers**: Ryan, Serena, Vivian, Aiden, Dylan, Eric, Uncle Fu, Ono Anna, and Sohee.
- **Zero-Shot Voice Cloning**: Analyzes spectral acoustic features from a 5-15s reference audio sample.
- **Voice Design**: Natural language prompt-to-voice timbre conditioning (e.g. "Deep raspy male narrator with slow tempo").
- **Dramatized Audiobook Converter (from WhiskeyCoder)**:
  - Document parsing: PDF (`pypdf`), EPUB (XHTML extraction), DOCX (XML parsing), and plain TXT/Markdown.
  - Smart boundary chunking: Preserves punctuation cadence without breaking sentence semantics.
  - Multi-speaker dramatization: Automatically assigns character quotes to dialogue voices and narration to narrator voices.
  - Batch job queue & automated audio concatenation.
- **C++ GGML High-Performance Backend (from qwentts.cpp)**: Native streaming support for CPU, CUDA, and quantized models.
- **ComfyUI Integration (from ComfyUI-FL-Qwen3TTS)**: Exportable custom nodes and ready-to-run workflow JSON templates.

---

## 3. Android Commander & Root Hub (awesome-android-root)
- **Pure Python ADB**: Powered by `adbutils` with embedded ADB binaries. Works seamlessly over USB and network TCP (`adb connect ip:port`).
- **Interactive Device Mirror**: Screen capture (`screencap -p`), click-to-tap coordinate mapping, and swipe gestures.
- **Root Operations Suite**:
  - Root shell execution (`su -c <cmd>`).
  - Detection of KernelSU, Magisk, and APatch frameworks.
  - Package debloater: Safely disable unwanted system apps and carrier bloatware via `pm disable-user --user 0`.
- **Virtual Device Sandbox**: Integrated Pixel 9 Pro (Android 15 / KernelSU) simulator for testing automation without physical hardware.
- **Awesome Android Root Catalog**: Curated offline database of 600+ root apps, Magisk modules, KernelSU modules, LSPosed hooks, and rooting guides.

---

## 4. OpenClaw Zero-Token & Provider Gateway
- **Zero-Token Web Gateway**: Reverse-proxy access to web LLM endpoints (Claude, ChatGPT, DeepSeek, Qwen, Gemini, Kimi, Grok) without API tokens.
- **BYOK / Standard Providers**: OpenAI, Anthropic, DeepSeek, Google Gemini, Groq, OpenRouter.
- **Local LLMs**: Seamless connection to Ollama (`localhost:11434`), vLLM (`localhost:8001`), and llama.cpp.
- **Failover Routing**: Automatic fallback cascade when tokens expire or rate limits occur.
