"""
ComfyUI-FL-Qwen3TTS Node Pack
Custom nodes for Alibaba Qwen3-TTS speech generation, voice cloning, and audiobooks.
"""

from app.audio.voices import PREDEFINED_VOICES, SUPPORTED_LANGUAGES, VoiceProfile
from app.audio.synthesis import SpeechSynthesizer

NODE_CLASS_MAPPINGS = {}
NODE_DISPLAY_NAME_MAPPINGS = {}


class ComfyUI_Qwen3TTS_CustomVoice:
    """Generate speech using predefined speakers."""
    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "text": ("STRING", {"multiline": True, "default": "Hello from OmniNexus ComfyUI node!"}),
                "speaker": (list(PREDEFINED_VOICES.keys()), {"default": "Ryan"}),
                "language": (SUPPORTED_LANGUAGES, {"default": "English"}),
                "speed": ("FLOAT", {"default": 1.0, "min": 0.5, "max": 2.0, "step": 0.05}),
            },
            "optional": {
                "instruct": ("STRING", {"default": ""})
            }
        }

    RETURN_TYPES = ("AUDIO",)
    RETURN_NAMES = ("audio",)
    FUNCTION = "generate"
    CATEGORY = "FL/Qwen3TTS"

    def generate(self, text, speaker, language, speed, instruct=None):
        voice = PREDEFINED_VOICES.get(speaker, PREDEFINED_VOICES["Ryan"])
        wav_bytes = SpeechSynthesizer.synthesize_wav(
            text=text,
            voice=voice,
            speed=speed,
            instruct=instruct
        )
        return ({"waveform": wav_bytes, "sample_rate": 24000},)


NODE_CLASS_MAPPINGS["FL_Qwen3TTS_CustomVoice"] = ComfyUI_Qwen3TTS_CustomVoice
NODE_DISPLAY_NAME_MAPPINGS["FL_Qwen3TTS_CustomVoice"] = "Qwen3-TTS Custom Voice (OmniNexus)"

__all__ = ["NODE_CLASS_MAPPINGS", "NODE_DISPLAY_NAME_MAPPINGS"]
