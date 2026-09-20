"""
Audiobook Converter Pipeline
Inspired by WhiskeyCoder/Qwen3-Audiobook-Converter.
Handles document extraction (PDF, EPUB, DOCX, TXT), sentence chunking,
multi-speaker dialogue tagging, progress tracking, and batch synthesis.
"""

import asyncio
import io
import re
import time
import uuid
import wave
import zipfile
import xml.etree.ElementTree as ET
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional
import pypdf

from app.audio.engine import tts_engine
from app.audio.voices import PREDEFINED_VOICES, VoiceProfile
from app.config import settings


class DocumentChunk:
    def __init__(self, index: int, text: str, speaker: str, is_dialogue: bool = False, chapter: str = "General"):
        self.index = index
        self.text = text
        self.speaker = speaker
        self.is_dialogue = is_dialogue
        self.chapter = chapter
        self.audio_data: Optional[bytes] = None
        self.status = "pending"  # "pending", "synthesized", "failed"


class AudiobookConversionJob:
    def __init__(self, job_id: str, title: str, chunks: List[DocumentChunk], narrator_voice: str, dialogue_voice: str):
        self.job_id = job_id
        self.title = title
        self.chunks = chunks
        self.narrator_voice = narrator_voice
        self.dialogue_voice = dialogue_voice
        self.total_chunks = len(chunks)
        self.completed_chunks = 0
        self.status = "initialized"  # "processing", "completed", "failed"
        self.output_path: Optional[str] = None
        self.created_at = time.time()
        self.error: Optional[str] = None


class AudiobookConverter:
    """Document-to-Audiobook processing engine."""

    def __init__(self):
        self.jobs: Dict[str, AudiobookConversionJob] = {}

    def parse_document(self, file_path: Path) -> str:
        """Extract plain text from PDF, EPUB, DOCX, or TXT."""
        suffix = file_path.suffix.lower()

        if suffix in [".txt", ".md"]:
            return file_path.read_text(encoding="utf-8", errors="replace")

        elif suffix == ".pdf":
            reader = pypdf.PdfReader(str(file_path))
            pages = []
            for page in reader.pages:
                text = page.extract_text()
                if text:
                    pages.append(text)
            return "\n\n".join(pages)

        elif suffix == ".docx":
            # Extract word/document.xml
            with zipfile.ZipFile(str(file_path)) as docx:
                xml_content = docx.read("word/document.xml")
                tree = ET.fromstring(xml_content)
                namespaces = {"w": "http://schemas.openxmlformats.org/wordprocessingml/2006/main"}
                paragraphs = []
                for p in tree.iterfind(".//w:p", namespaces):
                    texts = [node.text for node in p.iterfind(".//w:t", namespaces) if node.text]
                    if texts:
                        paragraphs.append("".join(texts))
                return "\n\n".join(paragraphs)

        elif suffix == ".epub":
            # Extract HTML/XHTML chapters from epub archive
            with zipfile.ZipFile(str(file_path)) as ep:
                text_parts = []
                for item in sorted(ep.namelist()):
                    if item.endswith((".html", ".xhtml", ".htm")):
                        raw = ep.read(item).decode("utf-8", errors="replace")
                        # Basic tag stripping
                        clean = re.sub(r"<[^>]+>", " ", raw)
                        clean = re.sub(r"\s+", " ", clean).strip()
                        if len(clean) > 50:
                            text_parts.append(clean)
                return "\n\n".join(text_parts)

        else:
            raise ValueError(f"Unsupported file format: {suffix}")

    def chunk_text(
        self,
        text: str,
        max_chars: int = 250,
        narrator: str = "Ryan",
        dialogue_speaker: str = "Vivian"
    ) -> List[DocumentChunk]:
        """
        Smart boundary text splitting with dialogue awareness.
        Quotes are assigned dialogue voice, narrative assigned narrator voice.
        """
        # Split into chapters if marked
        chapter_regex = r"(?:Chapter\s+\d+|Глава\s+\d+|Часть\s+\d+|SECTION\s+\d+)"
        raw_chapters = re.split(f"({chapter_regex})", text, flags=re.IGNORECASE)
        
        current_chapter = "Prologue"
        sections: List[Tuple[str, str]] = []  # (chapter_name, text)

        idx = 0
        while idx < len(raw_chapters):
            item = raw_chapters[idx].strip()
            if re.match(chapter_regex, item, re.IGNORECASE):
                current_chapter = item
                content = raw_chapters[idx + 1].strip() if idx + 1 < len(raw_chapters) else ""
                sections.append((current_chapter, content))
                idx += 2
            else:
                if item:
                    sections.append((current_chapter, item))
                idx += 1

        chunks: List[DocumentChunk] = []
        chunk_idx = 0

        for chap_title, sec_text in sections:
            # First split by paragraphs/lines
            lines = [l.strip() for l in sec_text.splitlines() if l.strip()]
            for line in lines:
                # Separate dialogue quotes from narrative text
                # Matches: "...", «...», “...”
                quote_pattern = r'(\"[^\"]+\"|«[^»]+»|“[^”]+”)'
                tokens = re.split(quote_pattern, line)
                
                for token in tokens:
                    token = token.strip()
                    if not token:
                        continue
                    
                    is_quote = (
                        (token.startswith('"') and token.endswith('"')) or
                        (token.startswith('«') and token.endswith('»')) or
                        (token.startswith('“') and token.endswith('”'))
                    )
                    speaker = dialogue_speaker if is_quote else narrator

                    # If token exceeds max_chars, split at clause boundaries
                    if len(token) > max_chars:
                        sub_parts = re.split(r"([,;:—])", token)
                        cur_buf = ""
                        for part in sub_parts:
                            if len(cur_buf) + len(part) < max_chars:
                                cur_buf += part
                            else:
                                if cur_buf.strip():
                                    chunks.append(DocumentChunk(chunk_idx, cur_buf.strip(), speaker, is_quote, chap_title))
                                    chunk_idx += 1
                                cur_buf = part
                        if cur_buf.strip():
                            chunks.append(DocumentChunk(chunk_idx, cur_buf.strip(), speaker, is_quote, chap_title))
                            chunk_idx += 1
                    else:
                        chunks.append(DocumentChunk(chunk_idx, token, speaker, is_quote, chap_title))
                        chunk_idx += 1

        return chunks

    async def create_conversion_job(
        self,
        title: str,
        text: str,
        narrator: str = "Ryan",
        dialogue_speaker: str = "Vivian",
        progress_cb: Optional[Callable[[AudiobookConversionJob], Any]] = None
    ) -> AudiobookConversionJob:
        """Create and start background audiobook conversion."""
        job_id = f"job-{uuid.uuid4().hex[:8]}"
        chunks = self.chunk_text(text, narrator=narrator, dialogue_speaker=dialogue_speaker)
        job = AudiobookConversionJob(
            job_id=job_id,
            title=title,
            chunks=chunks,
            narrator_voice=narrator,
            dialogue_voice=dialogue_speaker
        )
        self.jobs[job_id] = job

        # Fire background conversion
        asyncio.create_task(self._run_job(job, progress_cb))
        return job

    async def _run_job(self, job: AudiobookConversionJob, progress_cb: Optional[Callable[[AudiobookConversionJob], Any]] = None):
        job.status = "processing"
        audio_segments: List[bytes] = []

        try:
            for chunk in job.chunks:
                try:
                    wav_data = await tts_engine.generate(
                        text=chunk.text,
                        speaker=chunk.speaker,
                        speed=1.0
                    )
                    chunk.audio_data = wav_data
                    chunk.status = "synthesized"
                    audio_segments.append(wav_data)
                except Exception as ex:
                    chunk.status = "failed"

                job.completed_chunks += 1
                if progress_cb:
                    try:
                        res = progress_cb(job)
                        if asyncio.iscoroutine(res):
                            await res
                    except Exception:
                        pass

            # Concatenate all synthesized WAV chunks
            if audio_segments:
                combined_wav = self._concatenate_wavs(audio_segments)
                filename = f"{re.sub(r'[^a-zA-Z0-9_-]', '_', job.title)}_{job.job_id}.wav"
                out_path = settings.audiobooks_dir / filename
                out_path.write_bytes(combined_wav)
                job.output_path = str(out_path)
                job.status = "completed"
            else:
                job.status = "failed"
                job.error = "No audio segments synthesized"

        except Exception as e:
            job.status = "failed"
            job.error = str(e)

        if progress_cb:
            try:
                res = progress_cb(job)
                if asyncio.iscoroutine(res):
                    await res
            except Exception:
                pass

    def _concatenate_wavs(self, wav_bytes_list: List[bytes]) -> bytes:
        """Merge list of WAV byte streams into a unified WAV file."""
        if not wav_bytes_list:
            return b""

        frames_list = []
        sample_rate = 24000
        n_channels = 1
        sampwidth = 2

        for wb in wav_bytes_list:
            try:
                with wave.open(io.BytesIO(wb), "rb") as wf:
                    n_channels = wf.getnchannels()
                    sampwidth = wf.getsampwidth()
                    sample_rate = wf.getframerate()
                    frames_list.append(wf.readframes(wf.getnframes()))
            except Exception:
                continue

        out_io = io.BytesIO()
        with wave.open(out_io, "wb") as out_wf:
            out_wf.setnchannels(n_channels)
            out_wf.setsampwidth(sampwidth)
            out_wf.setframerate(sample_rate)
            for f in frames_list:
                out_wf.writeframes(f)

        return out_io.getvalue()

    def get_job(self, job_id: str) -> Optional[AudiobookConversionJob]:
        return self.jobs.get(job_id)


audiobook_converter = AudiobookConverter()
