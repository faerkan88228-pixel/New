"""
OmniNexus Studio - Unified Application Server
FastAPI Web Application, REST Endpoints, WebSocket Event Bus, and Static Mounts.
"""

import asyncio
import io
import json
import os
from pathlib import Path
from typing import Any, Dict, List, Optional

from fastapi import FastAPI, File, Form, HTTPException, UploadFile, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, HTMLResponse, Response
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from app.agent.channels import global_event_bus, AgentEvent
from app.agent.manus_core import manus_agent
from app.agent.memory import memory_manager
from app.agent.voice_agent import voice_agent
from app.android.bridge import android_bridge
from app.android.controller import android_controller
from app.android.knowledge_base import root_catalog
from app.audio.audiobook import audiobook_converter
from app.audio.comfyui_integration import comfyui_registry
from app.audio.engine import tts_engine
from app.audio.voices import PREDEFINED_VOICES, design_voice_from_prompt
from app.config import settings
from app.gateway.catalog import AVAILABLE_MODELS
from app.gateway.router import model_router
from app.gateway.zero_token import zero_token_gateway
from app.tools.base import tool_registry

# Initialize FastAPI app
app = FastAPI(
    title=settings.server.app_name,
    version=settings.server.version,
    description="Unified Autonomous Agent, Qwen3-TTS Voice Studio, and Android Commander Platform"
)

# Enable CORS for preview environment
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount static files
static_dir = settings.workspace_dir.parent.parent / "app" / "web" / "static"
static_dir.mkdir(parents=True, exist_ok=True)
app.mount("/static", StaticFiles(directory=str(static_dir)), name="static")

# Templates path
templates_dir = settings.workspace_dir.parent.parent / "app" / "web" / "templates"


# =============================================================================
# HTML FRONTEND ROOT
# =============================================================================

@app.get("/", response_class=HTMLResponse)
async def serve_index():
    index_file = templates_dir / "index.html"
    if index_file.exists():
        return HTMLResponse(content=index_file.read_text(encoding="utf-8"))
    return HTMLResponse(content="<h1>OmniNexus Studio Loading...</h1>")


# =============================================================================
# WEBSOCKET REAL-TIME STREAMING
# =============================================================================

class ConnectionManager:
    def __init__(self):
        self.active_connections: List[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)

    def disconnect(self, websocket: WebSocket):
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)

    async def broadcast(self, message: Dict[str, Any]):
        for connection in list(self.active_connections):
            try:
                await connection.send_json(message)
            except Exception:
                self.disconnect(connection)


ws_manager = ConnectionManager()

# Forward EventBus events to WebSocket clients
def event_broadcaster(event: AgentEvent):
    asyncio.create_task(ws_manager.broadcast({
        "channel": event.channel,
        "event_type": event.event_type,
        "payload": event.payload,
        "timestamp": event.timestamp
    }))

global_event_bus.subscribe("*", event_broadcaster)


@app.websocket("/ws/agent")
async def websocket_agent_endpoint(websocket: WebSocket):
    await ws_manager.connect(websocket)
    try:
        # Send recent events upon connection
        recent = global_event_bus.get_recent_events(limit=30)
        for ev in recent:
            await websocket.send_json({
                "channel": ev.channel,
                "event_type": ev.event_type,
                "payload": ev.payload,
                "timestamp": ev.timestamp
            })
        while True:
            data = await websocket.receive_text()
            # Handle client control messages
            try:
                msg = json.loads(data)
                if msg.get("action") == "ping":
                    await websocket.send_json({"type": "pong"})
            except Exception:
                pass
    except WebSocketDisconnect:
        ws_manager.disconnect(websocket)


# =============================================================================
# AGENT API
# =============================================================================

class AgentTaskRequest(BaseModel):
    goal: str
    session_id: Optional[str] = "default"


@app.post("/api/agent/task")
async def run_agent_task(req: AgentTaskRequest):
    sess_id = req.session_id or "default"
    result = await manus_agent.run_task(sess_id, req.goal)
    return result


@app.get("/api/agent/sessions")
async def list_agent_sessions():
    return memory_manager.list_sessions()


@app.get("/api/agent/sessions/{session_id}")
async def get_session_details(session_id: str):
    sess = memory_manager.get_session(session_id)
    if not sess:
        raise HTTPException(status_code=404, detail="Session not found")
    return sess


@app.post("/api/agent/sessions/new")
async def create_new_session(title: str = "New Task Session"):
    sess = memory_manager.create_session(title=title)
    return {"session_id": sess.session_id, "title": sess.title}


@app.get("/api/agent/tools")
async def list_available_tools():
    tools = tool_registry.list_tools()
    return [
        {
            "name": t.name,
            "description": t.description,
            "parameters": t.parameters
        }
        for t in tools
    ]


class VoiceTurnRequest(BaseModel):
    session_id: Optional[str] = "default"
    text: str
    speaker: Optional[str] = "Ryan"
    language: Optional[str] = "English"


@app.post("/api/agent/voice_turn")
async def agent_voice_turn(req: VoiceTurnRequest):
    res = await voice_agent.process_voice_turn(
        session_id=req.session_id or "default",
        user_text=req.text,
        speaker=req.speaker or "Ryan",
        language=req.language or "English"
    )
    return res


# =============================================================================
# QWEN3-TTS & AUDIOBOOK API
# =============================================================================

@app.get("/api/audio/voices")
async def list_voices():
    return tts_engine.list_voices()


class SynthesizeRequest(BaseModel):
    text: str
    speaker: Optional[str] = "Ryan"
    language: Optional[str] = "English"
    speed: Optional[float] = 1.0
    pitch: Optional[float] = 1.0
    instruct: Optional[str] = None
    voice_prompt: Optional[str] = None


@app.post("/api/audio/synthesize")
async def synthesize_speech(req: SynthesizeRequest):
    wav_bytes = await tts_engine.generate(
        text=req.text,
        speaker=req.speaker or "Ryan",
        language=req.language or "English",
        speed=req.speed or 1.0,
        pitch=req.pitch or 1.0,
        instruct=req.instruct,
        voice_prompt=req.voice_prompt
    )
    filename = f"tts_{os.urandom(4).hex()}.wav"
    file_path = settings.audiobooks_dir / filename
    file_path.write_bytes(wav_bytes)

    return {
        "success": True,
        "filename": filename,
        "url": f"/api/audio/file/{filename}",
        "size_bytes": len(wav_bytes)
    }


@app.post("/api/audio/clone")
async def clone_voice_from_sample(
    name: str = Form(...),
    reference_audio: UploadFile = File(...)
):
    audio_bytes = await reference_audio.read()
    profile = tts_engine.register_voice_clone(name, audio_bytes)
    return {
        "success": True,
        "voice": profile.model_dump()
    }


class VoiceDesignRequest(BaseModel):
    prompt: str


@app.post("/api/audio/design")
async def design_voice(req: VoiceDesignRequest):
    profile = design_voice_from_prompt(req.prompt)
    return {
        "success": True,
        "voice": profile.model_dump()
    }


@app.post("/api/audio/audiobook/upload")
async def upload_audiobook(
    file: UploadFile = File(...),
    title: str = Form("My Audiobook"),
    narrator: str = Form("Ryan"),
    dialogue: str = Form("Vivian")
):
    temp_path = settings.audiobooks_dir / f"temp_{os.urandom(4).hex()}_{file.filename}"
    content = await file.read()
    temp_path.write_bytes(content)

    try:
        doc_text = audiobook_converter.parse_document(temp_path)
    finally:
        if temp_path.exists():
            temp_path.unlink()

    job = await audiobook_converter.create_conversion_job(
        title=title,
        text=doc_text,
        narrator=narrator,
        dialogue_speaker=dialogue
    )

    return {
        "success": True,
        "job_id": job.job_id,
        "title": job.title,
        "total_chunks": job.total_chunks,
        "status": job.status
    }


@app.get("/api/audio/audiobook/jobs/{job_id}")
async def get_audiobook_job(job_id: str):
    job = audiobook_converter.get_job(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")

    download_url = None
    if job.output_path:
        filename = Path(job.output_path).name
        download_url = f"/api/audio/file/{filename}"

    return {
        "job_id": job.job_id,
        "title": job.title,
        "total_chunks": job.total_chunks,
        "completed_chunks": job.completed_chunks,
        "progress_percent": round((job.completed_chunks / max(1, job.total_chunks)) * 100, 1),
        "status": job.status,
        "download_url": download_url,
        "error": job.error
    }


@app.get("/api/audio/file/{filename}")
async def get_audio_file(filename: str):
    safe_name = os.path.basename(filename)
    file_path = settings.audiobooks_dir / safe_name
    if not file_path.exists():
        raise HTTPException(status_code=404, detail="Audio file not found")
    return FileResponse(file_path, media_type="audio/wav")


# =============================================================================
# ANDROID COMMANDER API
# =============================================================================

@app.get("/api/android/devices")
async def list_android_devices():
    return android_bridge.list_devices()


class ConnectDeviceRequest(BaseModel):
    address: str


@app.post("/api/android/connect")
async def connect_android_device(req: ConnectDeviceRequest):
    res = android_bridge.connect_network_device(req.address)
    return {"result": res}


@app.get("/api/android/info")
async def get_device_status(serial: Optional[str] = None):
    return android_controller.get_info(serial)


@app.get("/api/android/screenshot")
async def get_device_screenshot(serial: Optional[str] = None):
    b64 = android_controller.get_screenshot_base64(serial)
    return {"screenshot_base64": b64}


class TapRequest(BaseModel):
    x: int
    y: int
    serial: Optional[str] = None


@app.post("/api/android/tap")
async def tap_android_screen(req: TapRequest):
    out = android_controller.tap(req.x, req.y, req.serial)
    return {"result": out}


class SwipeRequest(BaseModel):
    x1: int
    y1: int
    x2: int
    y2: int
    serial: Optional[str] = None


@app.post("/api/android/swipe")
async def swipe_android_screen(req: SwipeRequest):
    out = android_controller.swipe(req.x1, req.y1, req.x2, req.y2, serial=req.serial)
    return {"result": out}


class KeyRequest(BaseModel):
    keycode: str
    serial: Optional[str] = None


@app.post("/api/android/key")
async def send_android_key(req: KeyRequest):
    out = android_controller.press_key(req.keycode, serial=req.serial)
    return {"result": out}


class TextRequest(BaseModel):
    text: str
    serial: Optional[str] = None


@app.post("/api/android/text")
async def send_android_text(req: TextRequest):
    out = android_controller.input_text(req.text, serial=req.serial)
    return {"result": out}


class ShellRequest(BaseModel):
    command: str
    as_root: bool = False
    serial: Optional[str] = None


@app.post("/api/android/shell")
async def execute_android_shell(req: ShellRequest):
    res = android_controller.execute_shell(req.command, as_root=req.as_root, serial=req.serial)
    return res


@app.get("/api/android/packages")
async def list_device_packages(serial: Optional[str] = None):
    return android_controller.list_packages(serial)


class TogglePackageRequest(BaseModel):
    package: str
    enable: bool
    serial: Optional[str] = None


@app.post("/api/android/package/toggle")
async def toggle_device_package(req: TogglePackageRequest):
    res = android_controller.toggle_package(req.package, req.enable, req.serial)
    return {"result": res}


@app.get("/api/android/catalog")
async def search_root_catalog(query: str = "", category: str = "", framework: str = ""):
    results = root_catalog.search(query=query, category=category, framework=framework)
    return {
        "total": len(results),
        "categories": root_catalog.get_categories(),
        "frameworks": root_catalog.get_frameworks(),
        "items": [r.model_dump() for r in results]
    }


# =============================================================================
# MODEL GATEWAY API
# =============================================================================

@app.get("/api/gateway/models")
async def get_available_models():
    return [m.model_dump() for m in AVAILABLE_MODELS.values()]


@app.get("/api/gateway/sessions")
async def get_zero_token_sessions():
    return zero_token_gateway.list_sessions()


class TestModelRequest(BaseModel):
    prompt: str
    model_id: Optional[str] = "qwen-2.5-72b"


@app.post("/api/gateway/test")
async def test_model_prompt(req: TestModelRequest):
    res = await model_router.complete(
        messages=[{"role": "user", "content": req.prompt}],
        model_id=req.model_id or "qwen-2.5-72b"
    )
    return res


# =============================================================================
# COMFYUI API
# =============================================================================

@app.get("/api/comfyui/nodes")
async def get_comfyui_nodes():
    return comfyui_registry.get_available_nodes()


@app.get("/api/comfyui/workflow/{workflow_type}")
async def export_comfyui_workflow(workflow_type: str = "custom_voice"):
    return comfyui_registry.generate_workflow_template(workflow_type)
