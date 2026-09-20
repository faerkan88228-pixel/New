"""
Session & Memory Management
Inspired by II-Agent session persistence and multi-turn state stores.
"""

import time
import uuid
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class ChatMessage(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4())[:8])
    role: str  # "system" | "user" | "assistant" | "tool"
    content: str
    name: Optional[str] = None
    tool_calls: Optional[List[Dict[str, Any]]] = None
    timestamp: float = Field(default_factory=time.time)


class SessionState(BaseModel):
    session_id: str
    title: str
    created_at: float = Field(default_factory=time.time)
    updated_at: float = Field(default_factory=time.time)
    messages: List[ChatMessage] = Field(default_factory=list)
    variables: Dict[str, Any] = Field(default_factory=dict)
    active_plan: Optional[Dict[str, Any]] = None


class MemoryManager:
    """Stores and retrieves conversational session history."""

    def __init__(self):
        self._sessions: Dict[str, SessionState] = {}
        # Create default session
        self.create_session("default", "Default Workspace Session")

    def create_session(self, session_id: Optional[str] = None, title: str = "New Session") -> SessionState:
        s_id = session_id or str(uuid.uuid4())[:8]
        session = SessionState(
            session_id=s_id,
            title=title,
            messages=[
                ChatMessage(
                    role="system",
                    content=(
                        "You are OmniNexus AI, an advanced unified autonomous agent combining OpenManus, "
                        "Kode Agent SDK, II-Agent, Qwen3-TTS Voice Studio, OpenClaw Gateway, and Android Commander. "
                        "You can execute shell commands, manage files, search the web, run Python code, "
                        "synthesize natural speech, convert audiobooks, and control Android devices."
                    )
                )
            ]
        )
        self._sessions[s_id] = session
        return session

    def get_session(self, session_id: str) -> Optional[SessionState]:
        return self._sessions.get(session_id)

    def list_sessions(self) -> List[Dict[str, Any]]:
        return [
            {
                "session_id": s.session_id,
                "title": s.title,
                "created_at": s.created_at,
                "updated_at": s.updated_at,
                "message_count": len(s.messages)
            }
            for s in sorted(self._sessions.values(), key=lambda x: x.updated_at, reverse=True)
        ]

    def add_message(self, session_id: str, role: str, content: str, name: Optional[str] = None, tool_calls: Optional[List[Dict[str, Any]]] = None) -> ChatMessage:
        session = self.get_session(session_id)
        if not session:
            session = self.create_session(session_id)
        msg = ChatMessage(role=role, content=content, name=name, tool_calls=tool_calls)
        session.messages.append(msg)
        session.updated_at = time.time()
        return msg

    def clear_session(self, session_id: str):
        if session_id in self._sessions:
            self._sessions[session_id].messages = [
                ChatMessage(role="system", content="Session reset.")
            ]
            self._sessions[session_id].updated_at = time.time()


memory_manager = MemoryManager()
