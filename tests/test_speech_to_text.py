import unittest
from unittest.mock import MagicMock

import speech_recognition as sr

from src.speech.exceptions import (
    SpeechInputTimeoutError,
    SpeechNotUnderstoodError,
    SpeechRecognitionServiceError,
)
from src.speech.speech_to_text import SpeechToText


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


class SpeechToTextTest(unittest.TestCase):
    def setUp(self) -> None:
        self.recognizer = MagicMock()
        self.microphone_factory = MagicMock(
            return_value=FakeMicrophone()
        )
        self.stt = SpeechToText(
            recognizer=self.recognizer,
            microphone_factory=(
                self.microphone_factory
            ),
            language="it-IT",
        )

    def test_listens_and_returns_transcription(
        self,
    ) -> None:
        audio = object()
        self.recognizer.listen.return_value = audio
        self.recognizer.recognize_google.return_value = (
            "Dove si trova il Martirio di sant'Orsola?"
        )

        result = self.stt.listen(
            timeout=4.0,
            phrase_time_limit=10.0,
        )

        self.assertEqual(
            result,
            "Dove si trova il Martirio di sant'Orsola?",
        )
        self.microphone_factory.assert_called_once_with()
        self.recognizer.adjust_for_ambient_noise\
            .assert_called_once_with(
                "audio-source",
                duration=0.5,
            )
        self.recognizer.listen.assert_called_once_with(
            "audio-source",
            timeout=4.0,
            phrase_time_limit=10.0,
        )
        self.recognizer.recognize_google\
            .assert_called_once_with(
                audio,
                language="it-IT",
            )

    def test_rejects_empty_transcription(self) -> None:
        self.recognizer.listen.return_value = object()
        self.recognizer.recognize_google.return_value = (
            "   "
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

    def test_converts_unknown_value_error(
        self,
    ) -> None:
        self.recognizer.listen.return_value = object()
        self.recognizer.recognize_google.side_effect = (
            sr.UnknownValueError()
        )

        with self.assertRaises(
            SpeechNotUnderstoodError
        ):
            self.stt.listen()

    def test_converts_service_error(self) -> None:
        self.recognizer.listen.return_value = object()
        self.recognizer.recognize_google.side_effect = (
            sr.RequestError("servizio non disponibile")
        )

        with self.assertRaises(
            SpeechRecognitionServiceError
        ):
            self.stt.listen()

    def test_validates_timeout(self) -> None:
        with self.assertRaises(ValueError):
            self.stt.listen(timeout=0)

    def test_validates_phrase_time_limit(
        self,
    ) -> None:
        with self.assertRaises(ValueError):
            self.stt.listen(phrase_time_limit=-1)


if __name__ == "__main__":
    unittest.main()
