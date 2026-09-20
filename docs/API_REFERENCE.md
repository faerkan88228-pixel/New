# OmniNexus Studio API Reference

The server exposes both REST endpoints and real-time WebSockets on port `8000`.

---

## 1. Agent Endpoints

### `POST /api/agent/task`
Run an autonomous multi-step task with the ReAct planning engine.
- **Request Body**:
  ```json
  {
    "goal": "Search recent news on AI agents and write a summary to workspace",
    "session_id": "default"
  }
  ```
- **Response**:
  ```json
  {
    "session_id": "default",
    "goal": "...",
    "status": "completed",
    "duration": 1.25,
    "steps": [...],
    "summary": "..."
  }
  ```

### `GET /api/agent/sessions`
List all active conversational sessions.

### `GET /api/agent/tools`
List all registered agent tools with JSON Schema parameters.

### `POST /api/agent/voice_turn`
Full-duplex conversational turn: generates text answer and synthesizes audible speech reply.

### `WebSocket /ws/agent`
Live streaming event channel broadcasting `progress`, `control`, and `monitor` events.

---

## 2. Audio & Speech Synthesis Endpoints

### `GET /api/audio/voices`
List all 9 predefined Qwen3-TTS voices and custom cloned voices.

### `POST /api/audio/synthesize`
Synthesize speech from text.
- **Request Body**:
  ```json
  {
    "text": "Hello world from OmniNexus Studio",
    "speaker": "Ryan",
    "language": "English",
    "speed": 1.0,
    "instruct": "calm narrator"
  }
  ```
- **Response**:
  ```json
  {
    "success": true,
    "filename": "tts_a1b2c3d4.wav",
    "url": "/api/audio/file/tts_a1b2c3d4.wav",
    "size_bytes": 149682
  }
  ```

### `POST /api/audio/clone`
Upload reference audio file (form-data: `reference_audio`, `name`) to clone timbre.

### `POST /api/audio/design`
Create custom voice profile from natural language description (`{"prompt": "Deep baritone male narrator"}`).

### `POST /api/audio/audiobook/upload`
Upload book document (`.pdf`, `.epub`, `.docx`, `.txt`) and start conversion.

### `GET /api/audio/audiobook/jobs/{job_id}`
Poll conversion progress and obtain download link for completed audiobook.

---

## 3. Android Commander Endpoints

### `GET /api/android/devices`
List physical USB/TCP devices and virtual sandbox device.

### `POST /api/android/connect`
Connect to network ADB device (`{"address": "192.168.1.100:5555"}`).

### `GET /api/android/info`
Get device model, Android release, battery, and root status (KernelSU/Magisk).

### `GET /api/android/screenshot`
Retrieve base64 PNG image of current screen state.

### `POST /api/android/tap`
Simulate tap event at coordinates (`{"x": 200, "y": 400}`).

### `POST /api/android/swipe`
Simulate swipe gesture (`{"x1": 200, "y1": 600, "x2": 200, "y2": 200}`).

### `POST /api/android/key`
Send Android key event (`{"keycode": "KEYCODE_HOME"}`).

### `POST /api/android/shell`
Run shell or root command (`{"command": "whoami", "as_root": true}`).

### `GET /api/android/packages`
List installed packages and debloat status.

### `POST /api/android/package/toggle`
Enable or debloat package (`{"package": "com.facebook.katana", "enable": false}`).

### `GET /api/android/catalog`
Search awesome-android-root database with query and category filters.

---

## 4. OpenClaw Model Gateway Endpoints

### `GET /api/gateway/models`
List catalog of 50+ supported models across Qwen, DeepSeek, Claude, GPT, Gemini, and Ollama.

### `GET /api/gateway/sessions`
List active Zero-Token web sessions.

### `POST /api/gateway/test`
Send test prompt to model gateway with latency tracking.

---

## 5. ComfyUI Endpoints

### `GET /api/comfyui/nodes`
List available ComfyUI custom nodes.

### `GET /api/comfyui/workflow/{workflow_type}`
Export ready-to-import ComfyUI workflow JSON template (`custom_voice`, `voice_clone`).
