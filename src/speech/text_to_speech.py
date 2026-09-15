import asyncio
import os
from io import BytesIO
from typing import Any, Callable

os.environ.setdefault(
    "PYGAME_HIDE_SUPPORT_PROMPT",
    "1",
)

import edge_tts
import pygame


VOICE_ITALIAN = "it-IT-IsabellaNeural"
VOICE_HINDI = "hi-IN-SwaraNeural"

DEFAULT_VOICE = VOICE_ITALIAN


class TextToSpeech:
    def __init__(
        self,
        voice: str = DEFAULT_VOICE,
        communicate_factory: Callable[..., Any] = (
            edge_tts.Communicate
        ),
        mixer=None,
        clock_factory=None,
    ) -> None:
        if not isinstance(voice, str):
            raise TypeError(
                "Il nome della voce deve essere una stringa"
            )

        clean_voice = voice.strip()

        if not clean_voice:
            raise ValueError(
                "Il nome della voce non puo essere vuoto"
            )

        if not callable(communicate_factory):
            raise TypeError(
                "communicate_factory deve essere chiamabile"
            )

        self._voice = clean_voice
        self._communicate_factory = communicate_factory
        self._mixer = (
            mixer
            if mixer is not None
            else pygame.mixer
        )
        self._clock_factory = (
            clock_factory
            if clock_factory is not None
            else pygame.time.Clock
        )

    def speak(self, text: str) -> None:
        if not isinstance(text, str):
            raise TypeError(
                "Il testo da pronunciare deve essere una stringa"
            )

        clean_text = text.strip()

        if not clean_text:
            raise ValueError(
                "Il testo da pronunciare non puo essere vuoto"
            )

        audio_buffer = asyncio.run(
            self._synthesize(clean_text)
        )

        self._play(audio_buffer)

    async def _synthesize(
        self,
        text: str,
    ) -> BytesIO:
        audio_buffer = BytesIO()

        communicate = self._communicate_factory(
            text=text,
            voice=self._voice,
        )

        async for chunk in communicate.stream():
            if chunk.get("type") == "audio":
                audio_buffer.write(
                    chunk["data"]
                )

        if audio_buffer.tell() == 0:
            raise RuntimeError(
                "Edge TTS non ha restituito audio"
            )

        audio_buffer.seek(0)

        return audio_buffer

    def _play(
        self,
        audio_buffer: BytesIO,
    ) -> None:
        self._mixer.init()

        try:
            self._mixer.music.load(
                audio_buffer,
                "mp3",
            )
            self._mixer.music.play()

            clock = self._clock_factory()

            while self._mixer.music.get_busy():
                clock.tick(20)
        finally:
            self._mixer.quit()
