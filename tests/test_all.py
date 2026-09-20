"""
Comprehensive Test Suite for OmniNexus Studio
Tests Agent Planning, Audio Synthesis, Audiobook Pipeline, Android Suite, and Model Gateway.
"""

import asyncio
import io
import unittest
import wave

from app.agent.channels import global_event_bus
from app.agent.manus_core import manus_agent
from app.agent.memory import memory_manager
from app.android.controller import android_controller
from app.android.knowledge_base import root_catalog
from app.audio.audiobook import audiobook_converter
from app.audio.engine import tts_engine
from app.audio.synthesis import SpeechSynthesizer
from app.audio.voices import PREDEFINED_VOICES, design_voice_from_prompt
from app.config import settings
from app.gateway.catalog import AVAILABLE_MODELS
from app.gateway.router import model_router
from app.tools.base import tool_registry


class TestOmniNexus(unittest.IsolatedAsyncioTestCase):

    async def test_tool_registry(self):
        """Verify all core agent tools are registered."""
        tools = tool_registry.list_tools()
        names = [t.name for t in tools]
        self.assertIn("bash", names)
        self.assertIn("file_operator", names)
        self.assertIn("web_search", names)
        self.assertIn("python_execute", names)
        self.assertIn("synthesize_speech", names)
        self.assertIn("android_device", names)
        self.assertIn("mcp_connector", names)

    async def test_bash_tool_execution(self):
        """Test terminal execution tool."""
        res = await tool_registry.execute_tool("bash", {"command": "echo 'Hello OmniNexus'"})
        self.assertTrue(res.success)
        self.assertIn("Hello OmniNexus", res.output)

    async def test_file_operator_tool(self):
        """Test file read/write operations."""
        write_res = await tool_registry.execute_tool(
            "file_operator",
            {"operation": "write", "path": "test_doc.txt", "content": "OmniNexus File System Test"}
        )
        self.assertTrue(write_res.success)

        read_res = await tool_registry.execute_tool(
            "file_operator",
            {"operation": "read", "path": "test_doc.txt"}
        )
        self.assertTrue(read_res.success)
        self.assertEqual(read_res.output, "OmniNexus File System Test")

    async def test_manus_react_agent_plan(self):
        """Test ReAct planning and step execution."""
        task_res = await manus_agent.run_task("test-session", "Search news about AI agents")
        self.assertEqual(task_res["status"], "completed")
        self.assertGreater(len(task_res["steps"]), 0)
        self.assertIn("Задача выполнена", task_res["summary"])

    async def test_audio_synthesis_and_wav(self):
        """Verify Qwen3-TTS acoustic synthesis generates valid 24kHz WAV audio."""
        wav_data = SpeechSynthesizer.synthesize_wav("Testing audio synthesis", PREDEFINED_VOICES["Ryan"])
        self.assertGreater(len(wav_data), 1000)
        with wave.open(io.BytesIO(wav_data), "rb") as wf:
            self.assertEqual(wf.getframerate(), 24000)
            self.assertEqual(wf.getnchannels(), 1)
            self.assertEqual(wf.getsampwidth(), 2)

    async def test_voice_design_from_prompt(self):
        """Test Qwen3-TTS voice design natural language parser."""
        voice = design_voice_from_prompt("A deep raspy baritone male narrator with slow tempo")
        self.assertEqual(voice.gender, "Male")
        self.assertLess(voice.base_pitch_hz, 120.0)
        self.assertLess(voice.speech_rate, 1.0)

    async def test_audiobook_converter_chunking_and_job(self):
        """Test document chunking with dialogue separation and audiobook creation."""
        story_text = (
            "Chapter 1: The Beginning\n\n"
            "The morning sun arose over the digital valley.\n"
            "\"Are we ready?\" asked Ryan.\n"
            "\"Always ready,\" replied Serena."
        )
        chunks = audiobook_converter.chunk_text(story_text, narrator="Ryan", dialogue_speaker="Serena")
        self.assertGreater(len(chunks), 1)
        dialogue_chunks = [c for c in chunks if c.is_dialogue]
        self.assertGreater(len(dialogue_chunks), 0)

        job = await audiobook_converter.create_conversion_job(
            title="Test Audiobook",
            text=story_text,
            narrator="Ryan",
            dialogue_speaker="Serena"
        )
        self.assertIsNotNone(job.job_id)
        # Wait briefly for conversion
        await asyncio.sleep(0.5)
        self.assertGreater(job.completed_chunks, 0)

    async def test_android_controller_and_catalog(self):
        """Test Android device controller, virtual device, and awesome-android-root search."""
        info = android_controller.get_info()
        self.assertTrue(info.get("is_rooted"))
        self.assertEqual(info.get("model"), "Pixel 9 Pro")

        # Test screen tap & shell
        tap_out = android_controller.tap(150, 250)
        self.assertIn("Simulated tap", tap_out)

        shell_res = android_controller.execute_shell("whoami", as_root=True)
        self.assertEqual(shell_res.get("exit_code"), 0)
        self.assertIn("root", shell_res.get("stdout"))

        # Test catalog search
        cat_results = root_catalog.search(query="magisk")
        self.assertGreater(len(cat_results), 0)

    async def test_model_router_and_catalog(self):
        """Test Model Gateway catalog and router."""
        self.assertIn("qwen-2.5-72b", AVAILABLE_MODELS)
        self.assertIn("deepseek-r1", AVAILABLE_MODELS)
        self.assertIn("claude-3-5-sonnet", AVAILABLE_MODELS)

        resp = await model_router.complete(
            messages=[{"role": "user", "content": "Hello"}],
            model_id="qwen-2.5-72b"
        )
        self.assertIn("content", resp)
        self.assertEqual(resp["provider_used"], "openclaw-zero-token")


if __name__ == "__main__":
    unittest.main()
