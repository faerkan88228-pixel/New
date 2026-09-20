"""
Acoustic Audio Synthesizer & Waveform Engine
Generates 24,000 Hz / 16-bit PCM WAV audio with phonetic modulation,
formant resonances, pitch inflections, and punctuation cadence.
"""

import io
import math
import struct
import wave
from typing import List, Optional, Tuple
import numpy as np
from app.audio.voices import VoiceProfile, PREDEFINED_VOICES


class SpeechSynthesizer:
    """Parametric phonetic speech synthesis engine."""

    SAMPLE_RATE = 24000  # Qwen3-TTS standard 24kHz

    @staticmethod
    def _split_into_phonetic_units(text: str) -> List[Tuple[str, float, bool]]:
        """
        Segment text into syllables, pauses, and cadence units.
        Returns list of (unit_token, duration_seconds, is_pause).
        """
        words = text.strip().split()
        units = []
        for word in words:
            clean_w = word.strip(".,!?:;\"'()«»—-")
            punct = word[-1] if word and word[-1] in ".,!?:;\"'()«»—" else ""
            
            # Estimate syllables
            syllables = max(1, len(clean_w) // 3)
            dur_per_syllable = 0.14
            for s in range(syllables):
                units.append((f"{clean_w}_{s}", dur_per_syllable, False))
                
            # Inter-word micro pause
            units.append(("space", 0.04, True))
            
            # Punctuation pause
            if punct in ".,;:":
                units.append(("comma_pause", 0.18, True))
            elif punct in "!?":
                units.append(("period_pause", 0.28, True))
                
        return units

    @classmethod
    def synthesize_wav(
        cls,
        text: str,
        voice: Optional[VoiceProfile] = None,
        speed: float = 1.0,
        pitch_scale: float = 1.0,
        instruct: Optional[str] = None
    ) -> bytes:
        """
        Synthesize speech from text and return WAV byte array.
        """
        if not voice:
            voice = PREDEFINED_VOICES["Ryan"]

        base_pitch = voice.base_pitch_hz * pitch_scale
        speech_rate = max(0.5, min(2.0, voice.speech_rate * speed))
        
        # Adjust dynamics based on instruction prompt (e.g. 'whisper', 'excited')
        if instruct:
            inst = instruct.lower()
            if "whisper" in inst or "soft" in inst:
                base_pitch *= 0.9
                voice_resonance = 0.4
            elif "excited" in inst or "happy" in inst:
                base_pitch *= 1.15
                speech_rate *= 1.12
                voice_resonance = 0.95
            else:
                voice_resonance = voice.resonance
        else:
            voice_resonance = voice.resonance

        units = cls._split_into_phonetic_units(text)
        if not units:
            # Minimal silence WAV
            return cls._empty_wav()

        total_samples = 0
        chunks: List[np.ndarray] = []

        total_units = len(units)
        for idx, (token, base_dur, is_pause) in enumerate(units):
            duration = base_dur / speech_rate
            num_samples = int(duration * cls.SAMPLE_RATE)
            if num_samples <= 0:
                continue

            if is_pause:
                # Add gentle noise floor or silence
                chunk = np.zeros(num_samples, dtype=np.float32)
            else:
                t = np.linspace(0, duration, num_samples, endpoint=False)
                
                # Pitch contour over the sentence / unit
                progress = idx / max(1, total_units)
                # Intonation inflection: declination with question lift
                inflection = 1.0 - 0.08 * math.sin(progress * math.pi)
                if "?" in text and progress > 0.8:
                    inflection += 0.18 * (progress - 0.8) / 0.2
                    
                cur_pitch = base_pitch * inflection
                
                # Formant frequencies for human voice simulation (F1, F2, F3)
                f1 = 500.0 * voice.formant_shift
                f2 = 1500.0 * voice.formant_shift
                f3 = 2500.0 * voice.formant_shift
                
                # Glottal source wave (harmonics)
                glottal = (
                    0.60 * np.sin(2.0 * np.pi * cur_pitch * t) +
                    0.25 * np.sin(2.0 * np.pi * 2.0 * cur_pitch * t) +
                    0.15 * np.sin(2.0 * np.pi * 3.0 * cur_pitch * t) +
                    0.08 * np.sin(2.0 * np.pi * 4.0 * cur_pitch * t)
                )
                
                # Formant resonators
                formant1 = np.sin(2.0 * np.pi * f1 * t) * np.exp(-3.0 * t)
                formant2 = np.sin(2.0 * np.pi * f2 * t) * np.exp(-4.0 * t)
                
                # Envelope: attack, sustain, decay
                attack_len = min(int(0.02 * cls.SAMPLE_RATE), num_samples // 3)
                decay_len = min(int(0.03 * cls.SAMPLE_RATE), num_samples // 3)
                env = np.ones(num_samples, dtype=np.float32)
                if attack_len > 0:
                    env[:attack_len] = np.linspace(0, 1, attack_len)
                if decay_len > 0:
                    env[-decay_len:] = np.linspace(1, 0, decay_len)
                    
                chunk = (glottal * 0.7 + (formant1 + formant2) * 0.3 * voice_resonance) * env
                
            chunks.append(chunk)

        full_audio = np.concatenate(chunks)
        # Normalize audio to -1.0 to 1.0
        max_val = np.max(np.abs(full_audio))
        if max_val > 0:
            full_audio = (full_audio / max_val) * 0.85

        # Convert to 16-bit PCM WAV
        pcm16 = (full_audio * 32767.0).astype(np.int16)
        
        wav_io = io.BytesIO()
        with wave.open(wav_io, "wb") as wf:
            wf.setnchannels(1)
            wf.setsampwidth(2)
            wf.setframerate(cls.SAMPLE_RATE)
            wf.writeframes(pcm16.tobytes())

        return wav_io.getvalue()

    @classmethod
    def _empty_wav(cls) -> bytes:
        wav_io = io.BytesIO()
        with wave.open(wav_io, "wb") as wf:
            wf.setnchannels(1)
            wf.setsampwidth(2)
            wf.setframerate(cls.SAMPLE_RATE)
            wf.writeframes(b"")
        return wav_io.getvalue()
