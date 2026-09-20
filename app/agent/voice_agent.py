"""
Full-Duplex Voice Agent
Handles bidirectional voice interaction: Audio in -> Agent Reasoning -> Qwen3-TTS Voice out.
"""

import uuid
from typing import Any, Dict, Optional
from app.agent.manus_core import manus_agent
from app.agent.memory import memory_manager
from app.audio.engine import tts_engine
from app.config import settings


class VoiceAgentDialog:
    """Coordinates conversational duplex audio interactions."""

    async def process_voice_turn(
        self,
        session_id: str,
        user_text: str,
        speaker: str = "Ryan",
        language: str = "English"
    ) -> Dict[str, Any]:
        """Process conversational turn and synthesize voice response."""
        # Save user message
        memory_manager.add_message(session_id, "user", user_text)

        # Run agent task / reasoning
        agent_result = await manus_agent.run_task(session_id, user_text)
        reply_text = agent_result.get("summary", "Task completed.")

        # Strip markdown syntax for natural voice synthesis
        clean_speech = reply_text.replace("#", "").replace("*", "").replace("`", "").replace("🎯", "")
        # Limit spoken answer length to avoid overly long speech
        speech_slice = clean_speech[:350].strip()

        # Synthesize audio response via Qwen3-TTS engine
        wav_bytes = await tts_engine.generate(
            text=speech_slice,
            speaker=speaker,
            language=language
        )

        audio_id = f"voice_reply_{uuid.uuid4().hex[:8]}.wav"
        audio_file = settings.audiobooks_dir / audio_id
        audio_file.write_bytes(wav_bytes)

        return {
            "session_id": session_id,
            "user_text": user_text,
            "assistant_text": reply_text,
            "audio_url": f"/api/audio/file/{audio_id}",
            "audio_filename": audio_id,
            "speaker": speaker
        }


voice_agent = VoiceAgentDialog()
