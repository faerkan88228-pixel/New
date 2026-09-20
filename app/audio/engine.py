"""
Unified Qwen3-TTS Engine
Combines Python parametric synthesis, qwentts.cpp GGML bindings, and remote API.
"""

import asyncio
import io
import math
import os
import subprocess
import time
import uuid
import wave
from pathlib import Path
from typing import Any, Dict, List, Optional
import httpx
import numpy as np

from app.audio.synthesis import SpeechSynthesizer
from app.audio.voices import (
    PREDEFINED_VOICES,
    SUPPORTED_LANGUAGES,
    VoiceProfile,
    design_voice_from_prompt,
)
from app.config import settings


class TTSEngine:
    """Unified Text-To-Speech orchestrator."""

    def __init__(self):
        self._cache: Dict[str, bytes] = {}
        self._cloned_voices: Dict[str, VoiceProfile] = {}

    def get_voice(self, name: str) -> VoiceProfile:
        if name in self._cloned_voices:
            return self._cloned_voices[name]
        return PREDEFINED_VOICES.get(name, PREDEFINED_VOICES["Ryan"])

    def list_voices(self) -> List[Dict[str, Any]]:
        result = []
        for v in PREDEFINED_VOICES.values():
            result.append({
                "name": v.name,
                "gender": v.gender,
                "language": v.language,
                "accent": v.accent,
                "description": v.description,
                "type": "predefined",
                "tags": v.tags
            })
        for v in self._cloned_voices.values():
            result.append({
                "name": v.name,
                "gender": v.gender,
                "language": v.language,
                "accent": v.accent,
                "description": v.description,
                "type": "cloned",
                "tags": v.tags
            })
        return result

    def register_voice_clone(self, name: str, audio_bytes: bytes, transcript: Optional[str] = None) -> VoiceProfile:
        """
        Extract acoustic properties from reference audio to create a cloned voice.
        Inspired by qwentts.cpp x-vector and ComfyUI-FL-Qwen3TTS voice clone node.
        """
        # Parse basic WAV properties or estimate from bytes
        try:
            with wave.open(io.BytesIO(audio_bytes), "rb") as wf:
                sr = wf.getframerate()
                frames = wf.readframes(min(sr * 5, wf.getnframes()))
                pcm_data = np.frombuffer(frames, dtype=np.int16)
                # Estimate pitch from zero crossings and power spectrum
                zero_crossings = np.nonzero(np.diff(pcm_data > 0))[0]
                if len(zero_crossings) > 20:
                    est_freq = (len(zero_crossings) / 2.0) / (len(pcm_data) / sr)
                    base_pitch = max(80.0, min(300.0, est_freq))
                else:
                    base_pitch = 140.0
        except Exception:
            base_pitch = 145.0

        gender = "Female" if base_pitch > 175.0 else "Male"
        formant = 1.15 if gender == "Female" else 0.94

        profile = VoiceProfile(
            name=name,
            gender=gender,
            language="Auto",
            accent="Cloned Profile",
            description=f"Cloned voice from audio ({len(audio_bytes)} bytes). Est. pitch: {base_pitch:.1f}Hz",
            base_pitch_hz=base_pitch,
            speech_rate=1.0,
            formant_shift=formant,
            resonance=0.92,
            tags=["cloned", gender.lower()]
        )
        self._cloned_voices[name] = profile
        return profile

    async def generate(
        self,
        text: str,
        speaker: str = "Ryan",
        language: str = "English",
        speed: float = 1.0,
        pitch: float = 1.0,
        instruct: Optional[str] = None,
        voice_prompt: Optional[str] = None
    ) -> bytes:
        """
        Generate audio WAV bytes for given text.
        """
        clean_text = text.strip()
        if not clean_text:
            return SpeechSynthesizer._empty_wav()

        # Voice selection or dynamic design
        if voice_prompt and voice_prompt.strip():
            voice = design_voice_from_prompt(voice_prompt)
        else:
            voice = self.get_voice(speaker)

        cache_key = f"{voice.name}:{speed}:{pitch}:{instruct}:{clean_text}"
        if settings.tts.enable_caching and cache_key in self._cache:
            return self._cache[cache_key]

        # 1. Check if qwentts.cpp binary exists and is executable
        qwentts_bin = Path(settings.tts.qwentts_bin_path)
        if qwentts_bin.exists() and os.access(qwentts_bin, os.X_OK):
            try:
                wav_data = await self._run_qwentts_cpp(qwentts_bin, clean_text, voice)
                if wav_data:
                    self._cache[cache_key] = wav_data
                    return wav_data
            except Exception:
                pass

        # 2. Check remote Qwen3 API if configured
        if settings.tts.qwen_api_url and settings.tts.qwen_api_url != "http://127.0.0.1:7860":
            try:
                wav_data = await self._call_qwen_api(clean_text, voice)
                if wav_data:
                    self._cache[cache_key] = wav_data
                    return wav_data
            except Exception:
                pass

        # 3. Parametric synthesis (instant, dependable fallback)
        wav_data = SpeechSynthesizer.synthesize_wav(
            text=clean_text,
            voice=voice,
            speed=speed,
            pitch_scale=pitch,
            instruct=instruct
        )
        self._cache[cache_key] = wav_data
        return wav_data

    async def _run_qwentts_cpp(self, binary: Path, text: str, voice: VoiceProfile) -> Optional[bytes]:
        tmp_out = settings.audiobooks_dir / f"tmp_cpp_{uuid.uuid4().hex[:8]}.wav"
        cmd = [
            str(binary),
            "-p", text,
            "-o", str(tmp_out),
            "--speaker", voice.name.lower()
        ]
        proc = await asyncio.create_subprocess_exec(*cmd, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE)
        await proc.communicate()
        if tmp_out.exists():
            data = tmp_out.read_bytes()
            tmp_out.unlink()
            return data
        return None

    async def _call_qwen_api(self, text: str, voice: VoiceProfile) -> Optional[bytes]:
        async with httpx.AsyncClient(timeout=10.0) as client:
            resp = await client.post(
                f"{settings.tts.qwen_api_url}/v1/audio/speech",
                json={"input": text, "voice": voice.name, "response_format": "wav"}
            )
            if resp.status_code == 200:
                return resp.content
        return None


tts_engine = TTSEngine()
