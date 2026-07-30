import unittest
from unittest.mock import MagicMock, patch

from src.speech.speech_to_text_factory import (
    create_speech_to_text,
)


class SpeechToTextFactoryTest(unittest.TestCase):
    @patch(
        "src.speech.speech_to_text_factory.SpeechToText"
    )
    def test_creates_google_engine(
        self,
        google_stt_class,
    ) -> None:
        google_stt = MagicMock()
        google_stt_class.return_value = google_stt

        result = create_speech_to_text("google")

        self.assertIs(result, google_stt)
        google_stt_class.assert_called_once_with()

    @patch(
        "src.speech.speech_to_text_factory."
        "WhisperSpeechToText"
    )
    def test_creates_whisper_engine(
        self,
        whisper_stt_class,
    ) -> None:
        whisper_stt = MagicMock()
        whisper_stt_class.return_value = whisper_stt

        result = create_speech_to_text("whisper")

        self.assertIs(result, whisper_stt)
        whisper_stt_class.assert_called_once_with()

    @patch(
        "src.speech.speech_to_text_factory."
        "WhisperSpeechToText"
    )
    def test_defaults_to_whisper(
        self,
        whisper_stt_class,
    ) -> None:
        whisper_stt = MagicMock()
        whisper_stt_class.return_value = whisper_stt

        result = create_speech_to_text(None)

        self.assertIs(result, whisper_stt)

    @patch(
        "src.speech.speech_to_text_factory."
        "WhisperSpeechToText"
    )
    def test_normalizes_engine_name(
        self,
        whisper_stt_class,
    ) -> None:
        whisper_stt = MagicMock()
        whisper_stt_class.return_value = whisper_stt

        result = create_speech_to_text("  WHISPER  ")

        self.assertIs(result, whisper_stt)

    def test_rejects_unknown_engine(self) -> None:
        with self.assertRaises(ValueError):
            create_speech_to_text("unknown")


if __name__ == "__main__":
    unittest.main()
