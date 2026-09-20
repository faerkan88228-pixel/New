"""
Qwen3-TTS Voice Registry & Profiles
Predefined speakers, voice design prompts, and acoustic profile definitions.
"""

from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class VoiceProfile(BaseModel):
    name: str
    gender: str
    language: str
    description: str
    accent: str = "Standard"
    base_pitch_hz: float = 160.0
    speech_rate: float = 1.0
    formant_shift: float = 1.0
    resonance: float = 0.8
    tags: List[str] = Field(default_factory=list)


# 9 Predefined Speakers from Qwen3-TTS CustomVoice model
PREDEFINED_VOICES: Dict[str, VoiceProfile] = {
    "Ryan": VoiceProfile(
        name="Ryan",
        gender="Male",
        language="English",
        accent="General American",
        description="Dynamic, authoritative male narrator, ideal for audiobooks, documentaries, and tech guides.",
        base_pitch_hz=125.0,
        speech_rate=1.02,
        formant_shift=0.95,
        resonance=0.9,
        tags=["audiobook", "narration", "confident", "english"]
    ),
    "Serena": VoiceProfile(
        name="Serena",
        gender="Female",
        language="Chinese",
        accent="Standard Mandarin",
        description="Warm, gentle female voice with clear articulation and melodic cadence.",
        base_pitch_hz=225.0,
        speech_rate=0.98,
        formant_shift=1.12,
        resonance=0.85,
        tags=["warm", "gentle", "chinese", "storytelling"]
    ),
    "Vivian": VoiceProfile(
        name="Vivian",
        gender="Female",
        language="Chinese",
        accent="Contemporary Urban",
        description="Bright, lively, expressive female voice with clear modern phrasing.",
        base_pitch_hz=240.0,
        speech_rate=1.08,
        formant_shift=1.18,
        resonance=0.88,
        tags=["lively", "bright", "conversational", "chinese"]
    ),
    "Aiden": VoiceProfile(
        name="Aiden",
        gender="Male",
        language="English",
        accent="US West Coast",
        description="Deep, calm, natural American male voice with steady conversational flow.",
        base_pitch_hz=115.0,
        speech_rate=0.95,
        formant_shift=0.92,
        resonance=0.92,
        tags=["deep", "calm", "podcast", "english"]
    ),
    "Dylan": VoiceProfile(
        name="Dylan",
        gender="Male",
        language="Chinese",
        accent="Beijing Dialect",
        description="Relaxed Beijing male speaker with authentic northern dialect coloring.",
        base_pitch_hz=135.0,
        speech_rate=1.00,
        formant_shift=0.97,
        resonance=0.82,
        tags=["dialect", "beijing", "casual", "chinese"]
    ),
    "Eric": VoiceProfile(
        name="Eric",
        gender="Male",
        language="Chinese",
        accent="Sichuan Dialect",
        description="Warm Sichuan male speaker with characteristic rhythmic tone.",
        base_pitch_hz=140.0,
        speech_rate=1.04,
        formant_shift=0.98,
        resonance=0.84,
        tags=["dialect", "sichuan", "friendly", "chinese"]
    ),
    "Uncle_Fu": VoiceProfile(
        name="Uncle_Fu",
        gender="Male",
        language="Chinese",
        accent="Mature Mandarin",
        description="Seasoned, mature male voice with deep resonance, ideal for historical fiction and audiobooks.",
        base_pitch_hz=105.0,
        speech_rate=0.92,
        formant_shift=0.88,
        resonance=0.95,
        tags=["mature", "deep", "narrator", "chinese"]
    ),
    "Ono_Anna": VoiceProfile(
        name="Ono_Anna",
        gender="Female",
        language="Japanese",
        accent="Tokyo Standard",
        description="Polite, melodious Japanese female voice with crisp syllable timing.",
        base_pitch_hz=235.0,
        speech_rate=1.05,
        formant_shift=1.15,
        resonance=0.87,
        tags=["japanese", "polite", "crisp"]
    ),
    "Sohee": VoiceProfile(
        name="Sohee",
        gender="Female",
        language="Korean",
        accent="Seoul Standard",
        description="Soft, natural Korean female speaker with gentle emotional depth.",
        base_pitch_hz=230.0,
        speech_rate=1.00,
        formant_shift=1.14,
        resonance=0.86,
        tags=["korean", "soft", "natural"]
    ),
    "Alex_RU": VoiceProfile(
        name="Alex_RU",
        gender="Male",
        language="Russian",
        accent="Standard Russian",
        description="Deep, confident Russian narrator with expressive intonation, perfect for literature and voice assistant.",
        base_pitch_hz=120.0,
        speech_rate=0.98,
        formant_shift=0.93,
        resonance=0.91,
        tags=["russian", "audiobook", "confident", "deep"]
    ),
    "Elena_RU": VoiceProfile(
        name="Elena_RU",
        gender="Female",
        language="Russian",
        accent="Standard Russian",
        description="Clear, expressive Russian female voice, warm and engaging for stories and dialogues.",
        base_pitch_hz=220.0,
        speech_rate=1.02,
        formant_shift=1.10,
        resonance=0.89,
        tags=["russian", "warm", "expressive", "assistant"]
    )
}

SUPPORTED_LANGUAGES = [
    "Russian",
    "English",
    "Chinese",
    "Japanese",
    "Korean",
    "German",
    "French",
    "Spanish",
    "Italian",
    "Portuguese"
]


def design_voice_from_prompt(prompt: str) -> VoiceProfile:
    """
    Qwen3-TTS Voice Design feature:
    Synthesize custom voice characteristics from a natural language prompt.
    E.g. 'A deep raspy male narrator with a slow, contemplative pace'
    """
    p_lower = prompt.lower()
    
    gender = "Male" if any(w in p_lower for w in ["male", "man", "guy", "baritone", "bass", "мужчина", "мужской", "дедушка"]) else "Female"
    
    # Pitch tuning
    if any(w in p_lower for w in ["deep", "low", "gravelly", "bass", "baritone", "глубокий", "низкий", "бас"]):
        pitch = 95.0 if gender == "Male" else 170.0
        formant = 0.88
    elif any(w in p_lower for w in ["high", "bright", "youthful", "young", "girl", "boy", "высокий", "звонкий"]):
        pitch = 160.0 if gender == "Male" else 260.0
        formant = 1.20
    else:
        pitch = 130.0 if gender == "Male" else 220.0
        formant = 1.0
        
    # Rate tuning
    if any(w in p_lower for w in ["slow", "calm", "contemplative", "whisper", "медленный", "спокойный"]):
        rate = 0.88
    elif any(w in p_lower for w in ["fast", "energetic", "hurried", "excited", "быстрый", "энергичный"]):
        rate = 1.18
    else:
        rate = 1.0

    lang = "Russian" if any(w in p_lower for w in ["russian", "русский", "русская", "россия"]) else "English"

    return VoiceProfile(
        name=f"Custom_Design_{abs(hash(prompt)) % 10000}",
        gender=gender,
        language=lang,
        description=f"Voice designed from: '{prompt}'",
        base_pitch_hz=pitch,
        speech_rate=rate,
        formant_shift=formant,
        resonance=0.9,
        tags=["custom_design"]
    )
