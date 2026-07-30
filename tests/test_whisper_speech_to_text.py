import unittest
from io import BytesIO
from unittest.mock import MagicMock

import speech_recognition as sr

from src.speech.exceptions import (
    SpeechInputTimeoutError,
    SpeechNotUnderstoodError,
    SpeechRecognitionServiceError,
)
from src.speech.whisper_speech_to_text import (
    WhisperSpeechToText,
)


class FakeMicrophone:
    def __enter__(self):
        return "audio-source"

    def __exit__(
        self,
        exc_type,
        exc_value,
        traceback,
    ):
        return False


class FakeAudio:
    def get_wav_data(self) -> bytes:
        return b"fake-wav-data"


class WhisperSpeechToTextTest(unittest.TestCase):
    def setUp(self) -> None:
        self.model = MagicMock()
        self.recognizer = MagicMock()
        self.recognizer.listen.return_value = FakeAudio()
        self.microphone_factory = MagicMock(
            return_value=FakeMicrophone()
        )

        self.stt = WhisperSpeechToText(
            model=self.model,
            recognizer=self.recognizer,
            microphone_factory=self.microphone_factory,
            language="it",
            pause_threshold=1.5,
        )

    def test_listens_and_returns_transcription(
        self,
    ) -> None:
        first_segment = MagicMock()
        first_segment.text = "Dove si trova "
        second_segment = MagicMock()
        second_segment.text = (
            "il Martirio di sant'Orsola?"
        )

        captured_audio = {}

        def transcribe(audio_stream, **kwargs):
            self.assertIsInstance(
                audio_stream,
                BytesIO,
            )
            captured_audio["data"] = (
                audio_stream.getvalue()
            )

            return (
                [first_segment, second_segment],
                MagicMock(),
            )

        self.model.transcribe.side_effect = transcribe

        result = self.stt.listen(
            timeout=4.0,
            phrase_time_limit=10.0,
        )

        self.assertEqual(
            result,
            "Dove si trova il Martirio di sant'Orsola?",
        )
        self.assertEqual(
            self.recognizer.pause_threshold,
            1.5,
        )
        self.recognizer.adjust_for_ambient_noise            .assert_called_once_with(
                "audio-source",
                duration=0.5,
            )
        self.recognizer.listen.assert_called_once_with(
            "audio-source",
            timeout=4.0,
            phrase_time_limit=10.0,
        )

        _, kwargs = self.model.transcribe.call_args
        self.assertEqual(
            captured_audio["data"],
            b"fake-wav-data",
        )
        self.assertEqual(kwargs["language"], "it")
        self.assertTrue(kwargs["vad_filter"])

    def test_rejects_empty_transcription(self) -> None:
        segment = MagicMock()
        segment.text = "   "
        self.model.transcribe.return_value = (
            [segment],
            MagicMock(),
        )

        with self.assertRaises(
            SpeechNotUnderstoodError
        ):
            self.stt.listen()

    def test_converts_listen_timeout(self) -> None:
        self.recognizer.listen.side_effect = (
            sr.WaitTimeoutError()
        )

        with self.assertRaises(
            SpeechInputTimeoutError
        ):
            self.stt.listen()

    def test_converts_model_error(self) -> None:
        self.model.transcribe.side_effect = RuntimeError(
            "modello non disponibile"
        )

        with self.assertRaises(
            SpeechRecognitionServiceError
        ):
            self.stt.listen()

    def test_validates_pause_threshold(self) -> None:
        with self.assertRaises(ValueError):
            WhisperSpeechToText(
                model=self.model,
                pause_threshold=0,
            )


if __name__ == "__main__":
    unittest.main()
