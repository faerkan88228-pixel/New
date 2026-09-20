"""
Voice Synthesis Tool for Agent
Allows the agent to generate audible speech deliverables or speak answers.
"""

import uuid
from typing import Any, Dict, Optional
from app.audio.engine import tts_engine
from app.audio.voices import PREDEFINED_VOICES
from app.config import settings
from app.tools.base import BaseTool, ToolResult


class TTSSpeechTool(BaseTool):
    name: str = "synthesize_speech"
    description: str = (
        "Synthesize natural spoken audio from text using Qwen3-TTS. "
        "Supports predefined voices (Ryan, Serena, Vivian, Aiden, Dylan, Uncle_Fu, Alex_RU, Elena_RU), "
        "custom voice design prompts, and saves audio to file."
    )
    parameters: Dict[str, Any] = {
        "type": "object",
        "properties": {
            "text": {
                "type": "string",
                "description": "The text to speak or narrate."
            },
            "speaker": {
                "type": "string",
                "enum": list(PREDEFINED_VOICES.keys()),
                "description": "Selected voice speaker. Default is 'Ryan'.",
                "default": "Ryan"
            },
            "language": {
                "type": "string",
                "description": "Language for speech synthesis (English, Russian, Chinese, etc.).",
                "default": "English"
            },
            "instruct": {
                "type": "string",
                "description": "Emotion or cadence instruction (e.g. 'calm narrator', 'excited', 'whispering')."
            },
            "voice_prompt": {
                "type": "string",
                "description": "Voice Design description for synthetic custom timbre."
            }
        },
        "required": ["text"]
    }

    async def execute(
        self,
        text: str,
        speaker: str = "Ryan",
        language: str = "English",
        instruct: Optional[str] = None,
        voice_prompt: Optional[str] = None,
        **kwargs
    ) -> ToolResult:
        try:
            wav_data = await tts_engine.generate(
                text=text,
                speaker=speaker,
                language=language,
                instruct=instruct,
                voice_prompt=voice_prompt
            )

            file_id = f"speech_{uuid.uuid4().hex[:8]}.wav"
            out_path = settings.audiobooks_dir / file_id
            out_path.write_bytes(wav_data)

            return ToolResult(
                success=True,
                output=(
                    f"Synthesized {len(wav_data)} bytes of audio using speaker '{speaker}'. "
                    f"Saved to: {out_path.name}. Audio is ready for playback."
                ),
                metadata={
                    "filename": file_id,
                    "url": f"/api/audio/file/{file_id}",
                    "size_bytes": len(wav_data),
                    "speaker": speaker
                }
            )

        except Exception as e:
            return ToolResult(success=False, output="", error=f"TTS synthesis error: {str(e)}")
