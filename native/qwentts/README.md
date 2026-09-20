# qwentts.cpp Native GGML Acceleration

This directory provides native C++ inference integration for **Qwen3-TTS** powered by GGML, based on `ServeurpersoCom/qwentts.cpp`.

## Features
- Ultra-low latency streaming synthesis on CPU, CUDA, Vulkan, and Metal
- Q4_K_M and Q8_0 quantization of Qwen3 Talker (0.6B and 1.7B)
- Zero-shot voice cloning with reference audio
- Voice design from text prompts
- HTTP streaming server integration

## Building from Source

```bash
cd native/qwentts
./build.sh
```

## Binary Auto-Detection
OmniNexus Studio automatically checks `native/qwentts/qwen-tts`. If found, it routes audio generation to the high-performance native GGML engine with fallback to the pure Python parametric synthesizer.
