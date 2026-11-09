"""Prometheus task bridge to the original, separately deployed OpenManus runtime.

The former keyword-based local planner is deliberately not used as a fallback:
a missing or unreachable real runtime is reported as an error instead of a mock success.
"""
import time
from typing import Any, Dict

from fastapi import HTTPException

from app.agent.channels import global_event_bus
from app.agent.memory import memory_manager
from app.agentic_workspace.runtime_client import run_openmanus_runtime
from app.agentic_workspace.service import get_agent_runtime_bundle


class ManusAgent:
    """Orchestrates workspace capability selection and delegates execution to OpenManus."""

    def __init__(self, name: str = "OpenManus"):
        self.name = name

    async def run_task(self, session_id: str, goal: str) -> Dict[str, Any]:
        start_time = time.time()
        await global_event_bus.emit_progress(
            "task_start",
            f"Starting OpenManus task: '{goal}'",
            session_id=session_id,
        )

        selected_capabilities: list[dict[str, Any]] = []
        runtime_contexts: list[dict[str, Any]] = []
        retrieval_mode = "base_only"
        try:
            runtime_bundle = await get_agent_runtime_bundle(goal)
            selected_capabilities = runtime_bundle["capabilities"]
            runtime_contexts = runtime_bundle["contexts"]
            retrieval_mode = runtime_bundle["retrieval_mode"]
        except Exception as exc:
            # The fixed base runtime can still run, but optional cloud overlays are unavailable.
            await global_event_bus.emit_monitor(
                "workspace_overlay_unavailable",
                {"reason": type(exc).__name__, "fallback": "base_openmanus_only"},
            )

        if selected_capabilities:
            await global_event_bus.emit_progress(
                "skills_selected",
                "Selected active repository capabilities",
                capabilities=selected_capabilities,
            )

        await global_event_bus.emit_monitor(
            "openmanus_runtime_started",
            {
                "skills_loaded": len(runtime_contexts),
                "capabilities_selected": len(selected_capabilities),
                "retrieval_mode": retrieval_mode,
            },
        )

        try:
            runtime_result = await run_openmanus_runtime(goal, runtime_contexts)
        except HTTPException as exc:
            await global_event_bus.emit_monitor(
                "openmanus_runtime_failed",
                {"status_code": exc.status_code, "reason": exc.detail},
            )
            raise

        duration = round(time.time() - start_time, 2)
        final_summary = str(runtime_result.get("output", "")).strip()
        if not final_summary:
            final_summary = "OpenManus завершил задачу без текстового итогового сообщения."

        memory_manager.add_message(session_id, "assistant", final_summary)
        await global_event_bus.emit_progress(
            "task_completed",
            f"OpenManus task finished in {duration}s",
            summary=final_summary,
            duration=duration,
        )
        await global_event_bus.emit_monitor(
            "task_metrics",
            {
                "duration_seconds": duration,
                "skills_loaded": len(runtime_contexts),
                "status": "success",
                "runtime": "openmanus",
            },
        )

        return {
            "session_id": session_id,
            "goal": goal,
            "status": "completed",
            "runtime": "openmanus",
            "retrieval_mode": retrieval_mode,
            "duration": duration,
            "steps": [],
            "selected_capabilities": selected_capabilities,
            "loaded_contexts": [
                {
                    "kind": item["kind"],
                    "name": item["name"],
                    "source_url": item["source_url"],
                    "source_sha": item["source_sha"],
                }
                for item in runtime_contexts
            ],
            "summary": final_summary,
        }


manus_agent = ManusAgent()
