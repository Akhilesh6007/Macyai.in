
"""Macy AI: Reliable chunked Edge TTS voiceover."""

import asyncio
import json
import logging
import re
import subprocess
import tempfile
import wave
from pathlib import Path

import aiohttp
import edge_tts
import imageio_ffmpeg

from edge_tts.exceptions import (
    NoAudioReceived,
    WebSocketError,
)

logger = logging.getLogger(__name__)

SAMPLE_RATE = 24000
TICKS_PER_SECOND = 10_000_000


def split_script(text, max_chars=260):
    """Split narration into short word-safe chunks."""

    text = re.sub(r"\s+", " ", text).strip()
    chunks = []
    current = ""

    for word in text.split():
        candidate = f"{current} {word}".strip()

        if current and len(candidate) > max_chars:
            chunks.append(current)
            current = word
        else:
            current = candidate

    if current:
        chunks.append(current)

    return chunks


async def synthesize_chunk(
    text, audio_file, metadata_file,
    voice, rate, volume,
):
    """Synthesize one chunk with limited retries."""

    for attempt in range(1, 4):
        audio_file.unlink(missing_ok=True)
        metadata_file.unlink(missing_ok=True)

        try:
            communicate = edge_tts.Communicate(
                text=text,
                voice=voice,
                rate=rate,
                volume=volume,
                boundary="WordBoundary",
                connect_timeout=15,
                receive_timeout=60,
            )

            await asyncio.wait_for(
                communicate.save(
                    str(audio_file),
                    str(metadata_file),
                ),
                timeout=120,
            )

            if (
                not audio_file.is_file()
                or audio_file.stat().st_size == 0
            ):
                raise NoAudioReceived(
                    "No audio returned"
                )

            if (
                not metadata_file.is_file()
                or metadata_file.stat().st_size == 0
            ):
                raise RuntimeError(
                    "Speech timing metadata is empty"
                )

            return

        except Exception as error:
            retryable = isinstance(
                error,
                (
                    NoAudioReceived,
                    WebSocketError,
                    aiohttp.ClientConnectionError,
                    asyncio.TimeoutError,
                ),
            )

            if isinstance(
                error, aiohttp.ClientResponseError
            ):
                retryable = error.status in (
                    429, 500, 502, 503, 504
                )

            logger.warning(
                "Edge TTS attempt %s/3 failed: %s",
                attempt,
                type(error).__name__,
            )

            if not retryable or attempt == 3:
                raise

            await asyncio.sleep(2 * attempt)


async def generate_voiceover(
    script: str,
    output_path: str | Path,
    voice: str = "en-AU-NatashaNeural",
    rate: str = "+0%",
    volume: str = "+0%",
):
    """Generate MP3 narration and aligned word timings."""

    if not isinstance(script, str) or not script.strip():
        raise ValueError("Voiceover script is empty")

    output_path = Path(output_path).resolve()
    output_path.parent.mkdir(
        parents=True, exist_ok=True
    )

    metadata_path = output_path.with_suffix(".jsonl")

    partial_audio = output_path.with_name(
        output_path.stem + ".partial.mp3"
    )
    partial_meta = metadata_path.with_name(
        metadata_path.stem + ".partial.jsonl"
    )

    chunks = split_script(script)
    ffmpeg = imageio_ffmpeg.get_ffmpeg_exe()

    try:
        with tempfile.TemporaryDirectory(
            prefix="macy_tts_",
            dir=output_path.parent,
        ) as folder:

            temp = Path(folder)
            full_wav = temp / "combined.wav"

            cumulative_frames = 0
            boundary_count = 0

            with (
                wave.open(str(full_wav), "wb") as combined,
                partial_meta.open(
                    "w", encoding="utf-8"
                ) as timing,
            ):
                combined.setnchannels(1)
                combined.setsampwidth(2)
                combined.setframerate(SAMPLE_RATE)

                for index, piece in enumerate(
                    chunks, start=1
                ):
                    logger.info(
                        "Edge TTS chunk %s/%s (%s chars)",
                        index,
                        len(chunks),
                        len(piece),
                    )

                    mp3 = temp / f"part_{index:03}.mp3"
                    meta = temp / f"part_{index:03}.jsonl"
                    wav = temp / f"part_{index:03}.wav"

                    await synthesize_chunk(
                        piece,
                        mp3,
                        meta,
                        voice,
                        rate,
                        volume,
                    )

                    conversion = subprocess.run(
                        [
                            ffmpeg,
                            "-y",
                            "-hide_banner",
                            "-loglevel", "error",
                            "-i", str(mp3),
                            "-ar", str(SAMPLE_RATE),
                            "-ac", "1",
                            "-c:a", "pcm_s16le",
                            str(wav),
                        ],
                        capture_output=True,
                        text=True,
                        timeout=120,
                    )

                    if conversion.returncode != 0:
                        raise RuntimeError(
                            "FFmpeg decoding failed: "
                            + conversion.stderr[-1500:]
                        )

                    with wave.open(str(wav), "rb") as source:
                        if (
                            source.getnchannels() != 1
                            or source.getsampwidth() != 2
                            or source.getframerate() != SAMPLE_RATE
                        ):
                            raise RuntimeError(
                                "Unexpected WAV format"
                            )

                        frames = source.getnframes()

                        if frames <= 0:
                            raise RuntimeError(
                                "Decoded audio chunk is empty"
                            )

                        data = source.readframes(frames)

                    time_shift = (
                        cumulative_frames * TICKS_PER_SECOND
                        // SAMPLE_RATE
                    )

                    for line in meta.read_text(
                        encoding="utf-8"
                    ).splitlines():
                        if not line.strip():
                            continue

                        event = json.loads(line)

                        if event.get("type") == "WordBoundary":
                            event["offset"] = (
                                int(event["offset"])
                                + time_shift
                            )

                            timing.write(
                                json.dumps(
                                    event,
                                    ensure_ascii=False,
                                ) + "\n"
                            )

                            boundary_count += 1

                    combined.writeframes(data)
                    cumulative_frames += frames

            if boundary_count == 0:
                raise RuntimeError(
                    "Edge TTS supplied no word timestamps"
                )

            encoding = subprocess.run(
                [
                    ffmpeg,
                    "-y",
                    "-hide_banner",
                    "-loglevel", "error",
                    "-i", str(full_wav),
                    "-c:a", "libmp3lame",
                    "-b:a", "96k",
                    str(partial_audio),
                ],
                capture_output=True,
                text=True,
                timeout=240,
            )

            if encoding.returncode != 0:
                raise RuntimeError(
                    "FFmpeg encoding failed: "
                    + encoding.stderr[-1500:]
                )

            if (
                not partial_audio.exists()
                or partial_audio.stat().st_size == 0
            ):
                raise RuntimeError(
                    "Final audio file is empty"
                )

            partial_audio.replace(output_path)
            partial_meta.replace(metadata_path)

        return {
            "audio_path": str(output_path),
            "metadata_path": str(metadata_path),
            "voice": voice,
        }

    finally:
        partial_audio.unlink(missing_ok=True)
        partial_meta.unlink(missing_ok=True)


def generate_voiceover_sync(
    script: str,
    output_path: str | Path,
    voice: str = "en-AU-NatashaNeural",
    rate: str = "+0%",
    volume: str = "+0%",
):
    """Synchronous entry point for Macy AI jobs."""

    return asyncio.run(
        generate_voiceover(
            script=script,
            output_path=output_path,
            voice=voice,
            rate=rate,
            volume=volume,
        )
    )
