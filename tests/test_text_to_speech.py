import unittest
from unittest.mock import MagicMock

from src.speech.text_to_speech import (
    DEFAULT_VOICE,
    VOICE_HINDI,
    VOICE_ITALIAN,
    TextToSpeech,
)


class FakeCommunicate:
    def __init__(
        self,
        chunks,
    ) -> None:
        self._chunks = chunks

    async def stream(self):
        for chunk in self._chunks:
            yield chunk


class TextToSpeechTest(unittest.TestCase):
    def setUp(self) -> None:
        self.mixer = MagicMock()
        self.clock = MagicMock()
        self.clock_factory = MagicMock(
            return_value=self.clock
        )

        self.mixer.music.get_busy.side_effect = [
            True,
            False,
        ]

    def _build_tts(
        self,
        voice=DEFAULT_VOICE,
        chunks=None,
    ):
        if chunks is None:
            chunks = [
                {
                    "type": "audio",
                    "data": b"fake-mp3-data",
                }
            ]

        communicate_factory = MagicMock(
            return_value=FakeCommunicate(
                chunks
            )
        )

        tts = TextToSpeech(
            voice=voice,
            communicate_factory=communicate_factory,
            mixer=self.mixer,
            clock_factory=self.clock_factory,
        )

        return tts, communicate_factory

    def test_uses_italian_voice_as_default(
        self,
    ) -> None:
        self.assertEqual(
            DEFAULT_VOICE,
            VOICE_ITALIAN,
        )
        self.assertEqual(
            VOICE_ITALIAN,
            "it-IT-IsabellaNeural",
        )

    def test_exposes_hindi_voice(
        self,
    ) -> None:
        self.assertEqual(
            VOICE_HINDI,
            "hi-IN-SwaraNeural",
        )

    def test_speaks_text_with_default_voice(
        self,
    ) -> None:
        tts, communicate_factory = (
            self._build_tts()
        )

        tts.speak(
            "Il dipinto si trova a Napoli."
        )

        communicate_factory.assert_called_once_with(
            text="Il dipinto si trova a Napoli.",
            voice=VOICE_ITALIAN,
        )

        self.mixer.init.assert_called_once_with()
        self.mixer.music.play.assert_called_once_with()
        self.mixer.quit.assert_called_once_with()

    def test_can_use_hindi_voice(
        self,
    ) -> None:
        tts, communicate_factory = (
            self._build_tts(
                voice=VOICE_HINDI,
            )
        )

        tts.speak(
            "Questa frase viene letta da Swara."
        )

        communicate_factory.assert_called_once_with(
            text=(
                "Questa frase viene letta da Swara."
            ),
            voice=VOICE_HINDI,
        )

    def test_strips_text_before_synthesis(
        self,
    ) -> None:
        tts, communicate_factory = (
            self._build_tts()
        )

        tts.speak(
            "  Buongiorno  "
        )

        communicate_factory.assert_called_once_with(
            text="Buongiorno",
            voice=VOICE_ITALIAN,
        )

    def test_loads_audio_from_memory_as_mp3(
        self,
    ) -> None:
        tts, _ = self._build_tts()

        tts.speak("Prova audio.")

        args = (
            self.mixer.music.load.call_args.args
        )

        self.assertEqual(
            args[1],
            "mp3",
        )

        audio_buffer = args[0]

        self.assertEqual(
            audio_buffer.getvalue(),
            b"fake-mp3-data",
        )

    def test_waits_until_playback_finishes(
        self,
    ) -> None:
        tts, _ = self._build_tts()

        tts.speak("Prova audio.")

        self.clock_factory.assert_called_once_with()
        self.clock.tick.assert_called_once_with(
            20
        )

    def test_rejects_empty_text(
        self,
    ) -> None:
        tts, _ = self._build_tts()

        with self.assertRaises(ValueError):
            tts.speak("   ")

    def test_rejects_non_string_text(
        self,
    ) -> None:
        tts, _ = self._build_tts()

        with self.assertRaises(TypeError):
            tts.speak(None)

    def test_rejects_empty_voice(
        self,
    ) -> None:
        with self.assertRaises(ValueError):
            TextToSpeech(
                voice="   ",
                mixer=self.mixer,
            )

    def test_rejects_non_string_voice(
        self,
    ) -> None:
        with self.assertRaises(TypeError):
            TextToSpeech(
                voice=None,
                mixer=self.mixer,
            )

    def test_rejects_invalid_communicate_factory(
        self,
    ) -> None:
        with self.assertRaises(TypeError):
            TextToSpeech(
                communicate_factory=None,
                mixer=self.mixer,
            )

    def test_raises_when_edge_returns_no_audio(
        self,
    ) -> None:
        tts, _ = self._build_tts(
            chunks=[
                {
                    "type": "WordBoundary",
                    "text": "test",
                }
            ]
        )

        with self.assertRaises(RuntimeError):
            tts.speak("Prova senza audio.")


if __name__ == "__main__":
    unittest.main()
