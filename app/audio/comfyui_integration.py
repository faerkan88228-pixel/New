"""
ComfyUI-FL-Qwen3TTS Integration & Workflow Exporter
Exposes modular node definitions and generates ComfyUI workflow JSON templates.
"""

import json
from typing import Any, Dict, List
from app.audio.voices import PREDEFINED_VOICES, SUPPORTED_LANGUAGES


class ComfyUINodeRegistry:
    """Provides node metadata and JSON workflow generation for ComfyUI."""

    @staticmethod
    def get_available_nodes() -> List[Dict[str, Any]]:
        return [
            {
                "name": "FL_Qwen3TTS_ModelLoader",
                "category": "FL/Qwen3TTS",
                "inputs": {
                    "model_name": ["Qwen3-TTS-12Hz-1.7B-CustomVoice", "Qwen3-TTS-12Hz-1.7B-Base", "Qwen3-TTS-12Hz-1.7B-VoiceDesign"],
                    "precision": ["bfloat16", "float16", "float32"],
                    "device": ["cuda", "cpu", "mps"]
                },
                "outputs": ["QWEN3TTS_MODEL"],
                "description": "Loads and caches Qwen3-TTS checkpoints from HuggingFace / Local GGML"
            },
            {
                "name": "FL_Qwen3TTS_CustomVoice",
                "category": "FL/Qwen3TTS",
                "inputs": {
                    "model": "QWEN3TTS_MODEL",
                    "text": "STRING",
                    "speaker": list(PREDEFINED_VOICES.keys()),
                    "language": SUPPORTED_LANGUAGES,
                    "temperature": "FLOAT",
                    "instruct": "STRING"
                },
                "outputs": ["AUDIO"],
                "description": "Generates speech using 9 predefined speakers with optional emotion/style prompt"
            },
            {
                "name": "FL_Qwen3TTS_VoiceClone",
                "category": "FL/Qwen3TTS",
                "inputs": {
                    "model": "QWEN3TTS_MODEL",
                    "text": "STRING",
                    "reference_audio": "AUDIO",
                    "reference_text": "STRING",
                    "language": SUPPORTED_LANGUAGES
                },
                "outputs": ["AUDIO"],
                "description": "Clones reference speaker timbre from 5-15s audio sample"
            },
            {
                "name": "FL_Qwen3TTS_VoiceDesign",
                "category": "FL/Qwen3TTS",
                "inputs": {
                    "model": "QWEN3TTS_MODEL",
                    "text": "STRING",
                    "design_prompt": "STRING",
                    "language": SUPPORTED_LANGUAGES
                },
                "outputs": ["AUDIO"],
                "description": "Synthesizes custom speaker from natural language description"
            },
            {
                "name": "FL_Qwen3TTS_AudiobookPipeline",
                "category": "FL/Qwen3TTS",
                "inputs": {
                    "model": "QWEN3TTS_MODEL",
                    "document_text": "STRING",
                    "narrator_speaker": list(PREDEFINED_VOICES.keys()),
                    "dialogue_speaker": list(PREDEFINED_VOICES.keys()),
                    "chunk_size": "INT"
                },
                "outputs": ["AUDIO", "TRANSCRIPT"],
                "description": "Dramatized multi-speaker audiobook chapter generator"
            }
        ]

    @staticmethod
    def generate_workflow_template(workflow_type: str = "custom_voice") -> Dict[str, Any]:
        """
        Generate a complete importable ComfyUI workflow JSON.
        """
        if workflow_type == "voice_clone":
            return {
                "last_node_id": 4,
                "nodes": [
                    {
                        "id": 1,
                        "type": "FL_Qwen3TTS_ModelLoader",
                        "pos": [100, 150],
                        "size": [280, 120],
                        "widgets_values": ["Qwen3-TTS-12Hz-1.7B-Base", "bfloat16", "cuda"]
                    },
                    {
                        "id": 2,
                        "type": "LoadAudio",
                        "pos": [100, 320],
                        "size": [280, 140],
                        "widgets_values": ["reference_voice_sample.wav"]
                    },
                    {
                        "id": 3,
                        "type": "FL_Qwen3TTS_VoiceClone",
                        "pos": [450, 180],
                        "size": [340, 240],
                        "inputs": [
                            {"name": "model", "type": "QWEN3TTS_MODEL", "link": [1, 0]},
                            {"name": "reference_audio", "type": "AUDIO", "link": [2, 0]}
                        ],
                        "widgets_values": ["Welcome to OmniNexus voice clone pipeline.", "", "English"]
                    },
                    {
                        "id": 4,
                        "type": "SaveAudio",
                        "pos": [850, 180],
                        "size": [260, 120],
                        "inputs": [{"name": "audio", "type": "AUDIO", "link": [3, 0]}],
                        "widgets_values": ["qwen3_cloned_output"]
                    }
                ],
                "links": [
                    [1, 1, 0, 3, 0, "QWEN3TTS_MODEL"],
                    [2, 2, 0, 3, 1, "AUDIO"],
                    [3, 3, 0, 4, 0, "AUDIO"]
                ]
            }
        else:
            # Default custom voice workflow
            return {
                "last_node_id": 3,
                "nodes": [
                    {
                        "id": 1,
                        "type": "FL_Qwen3TTS_ModelLoader",
                        "pos": [120, 180],
                        "size": [300, 130],
                        "widgets_values": ["Qwen3-TTS-12Hz-1.7B-CustomVoice", "bfloat16", "cuda"]
                    },
                    {
                        "id": 2,
                        "type": "FL_Qwen3TTS_CustomVoice",
                        "pos": [480, 180],
                        "size": [340, 260],
                        "inputs": [
                            {"name": "model", "type": "QWEN3TTS_MODEL", "link": [1, 0]}
                        ],
                        "widgets_values": [
                            "OmniNexus brings together autonomous agents, voice intelligence, and Android automation.",
                            "Ryan",
                            "English",
                            0.85,
                            "Warm and confident audiobook tone"
                        ]
                    },
                    {
                        "id": 3,
                        "type": "SaveAudio",
                        "pos": [880, 180],
                        "size": [260, 120],
                        "inputs": [{"name": "audio", "type": "AUDIO", "link": [2, 0]}],
                        "widgets_values": ["omninexus_speech_output"]
                    }
                ],
                "links": [
                    [1, 1, 0, 2, 0, "QWEN3TTS_MODEL"],
                    [2, 2, 0, 3, 0, "AUDIO"]
                ]
            }


comfyui_registry = ComfyUINodeRegistry()
