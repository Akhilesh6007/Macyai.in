
"""
Macy AI - Reliable Edge TTS Voiceover Service

Features:
- Automatic retries for temporary errors
- Timeout protection
- Partial file cleanup
- WordBoundary metadata for subtitles
- Useful backend error logging
"""

import asyncio
import logging
from pathlib import Path

import aiohttp
import edge_tts
from edge_tts.exceptions import (
    NoAudioReceived,
    WebSocketError,
)

logger = logging.getLogger(__name__)

MAX_RETRIES = 3


async def generate_voiceover(
    script: str,
    output_path: str | Path,
    voice: str = "en-AU-NatashaNeural",
    rate: str = "+0%",
    volume: str = "+0%",
):
    if not isinstance(script, str) or not script.strip():
        raise ValueError("Voiceover script is empty.")

    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    metadata_path = output_path.with_suffix(".jsonl")

    temp_audio = output_path.with_name(
        output_path.name + ".partial"
    )
    temp_metadata = metadata_path.with_name(
        metadata_path.name + ".partial"
    )

    for attempt in range(1, MAX_RETRIES + 1):
        try:
            logger.info(
                "Edge TTS attempt %d/%d",
                attempt,
                MAX_RETRIES,
            )

            # Remove partial files from earlier attempts.
            temp_audio.unlink(missing_ok=True)
            temp_metadata.unlink(missing_ok=True)

            # A new communicator is required for each retry.
            communicate = edge_tts.Communicate(
                text=script.strip(),
                voice=voice,
                rate=rate,
                volume=volume,
                boundary="WordBoundary",
                connect_timeout=15,
                receive_timeout=60,
            )

            await asyncio.wait_for(
                communicate.save(
                    str(temp_audio),
                    str(temp_metadata),
                ),
                timeout=180,
            )

            if (
                not temp_audio.is_file()
                or temp_audio.stat().st_size == 0
            ):
                raise NoAudioReceived(
                    "No audio was generated."
                )

            if (
                not temp_metadata.is_file()
                or temp_metadata.stat().st_size == 0
            ):
                raise RuntimeError(
                    "Speech timing metadata is missing."
                )

            temp_audio.replace(output_path)
            temp_metadata.replace(metadata_path)

            logger.info("Edge TTS voiceover completed")

            return {
                "audio_path": str(output_path),
                "metadata_path": str(metadata_path),
                "voice": voice,
            }

        except Exception as error:
            temp_audio.unlink(missing_ok=True)
            temp_metadata.unlink(missing_ok=True)

            status = getattr(error, "status", None)

            logger.warning(
                "Edge TTS failed: attempt=%d, type=%s, "
                "http_status=%s",
                attempt,
                type(error).__name__,
                status,
            )

            # Retry only potentially temporary failures.
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
                    500, 502, 503, 504
                )

            if not retryable or attempt >= MAX_RETRIES:
                raise

            delay = attempt * 2

            logger.warning(
                "Retrying Edge TTS after %s seconds",
                delay,
            )

            await asyncio.sleep(delay)


def generate_voiceover_sync(
    script: str,
    output_path: str | Path,
    voice: str = "en-AU-NatashaNeural",
    rate: str = "+0%",
    volume: str = "+0%",
):
    return asyncio.run(
        generate_voiceover(
            script=script,
            output_path=output_path,
            voice=voice,
            rate=rate,
            volume=volume,
        )
    )
