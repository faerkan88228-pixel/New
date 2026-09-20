"""
Kode Agent SDK Event Channels
Three-channel architecture: Progress, Control, Monitor.
Provides real-time event streaming for UI subscribers and agent control.
"""

import asyncio
import time
from typing import Any, Callable, Dict, List, Optional
from pydantic import BaseModel, Field


class AgentEvent(BaseModel):
    id: str
    channel: str  # "progress" | "control" | "monitor"
    event_type: str
    timestamp: float = Field(default_factory=time.time)
    payload: Dict[str, Any] = Field(default_factory=dict)


class EventBus:
    """EventBus coordinating Progress, Control, and Monitor events."""

    def __init__(self):
        self._subscribers: Dict[str, List[Callable[[AgentEvent], Any]]] = {
            "progress": [],
            "control": [],
            "monitor": [],
            "all": []
        }
        self._history: List[AgentEvent] = []
        self._event_counter: int = 0
        self._lock = asyncio.Lock()

    def subscribe(self, channel: str, callback: Callable[[AgentEvent], Any]):
        if channel in self._subscribers:
            self._subscribers[channel].append(callback)
        elif channel == "*":
            self._subscribers["all"].append(callback)

    def unsubscribe(self, channel: str, callback: Callable[[AgentEvent], Any]):
        if channel in self._subscribers and callback in self._subscribers[channel]:
            self._subscribers[channel].remove(callback)
        elif channel == "*" and callback in self._subscribers["all"]:
            self._subscribers["all"].remove(callback)

    async def emit(self, channel: str, event_type: str, payload: Dict[str, Any]) -> AgentEvent:
        async with self._lock:
            self._event_counter += 1
            event = AgentEvent(
                id=f"evt-{self._event_counter:06d}",
                channel=channel,
                event_type=event_type,
                payload=payload
            )
            self._history.append(event)
            # Cap history to prevent memory leak
            if len(self._history) > 2000:
                self._history.pop(0)

        # Notify subscribers
        callbacks = list(self._subscribers.get(channel, [])) + list(self._subscribers.get("all", []))
        for cb in callbacks:
            try:
                res = cb(event)
                if asyncio.iscoroutine(res):
                    asyncio.create_task(res)
            except Exception as e:
                pass
        return event

    # Convenience channel publishers
    async def emit_progress(self, event_type: str, message: str, **kwargs):
        payload = {"message": message, **kwargs}
        return await self.emit("progress", event_type, payload)

    async def emit_control(self, event_type: str, action: str, **kwargs):
        payload = {"action": action, **kwargs}
        return await self.emit("control", event_type, payload)

    async def emit_monitor(self, event_type: str, metrics: Dict[str, Any], **kwargs):
        payload = {"metrics": metrics, **kwargs}
        return await self.emit("monitor", event_type, payload)

    def get_recent_events(self, limit: int = 100) -> List[AgentEvent]:
        return self._history[-limit:]


# Global event bus singleton
global_event_bus = EventBus()
