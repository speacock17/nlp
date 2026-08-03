import unittest
from unittest.mock import MagicMock

from src.speech.text_to_speech import TextToSpeech


class TextToSpeechTest(unittest.TestCase):
    def setUp(self) -> None:
        self.engine = MagicMock()
        self.tts = TextToSpeech(
            engine=self.engine,
            rate=170,
            volume=0.9,
        )

    def test_configures_rate_and_volume(self) -> None:
        self.engine.setProperty.assert_any_call(
            "rate",
            170,
        )
        self.engine.setProperty.assert_any_call(
            "volume",
            0.9,
        )

    def test_speaks_text(self) -> None:
        self.tts.speak(
            "Il dipinto si trova a Napoli."
        )

        self.engine.say.assert_called_once_with(
            "Il dipinto si trova a Napoli."
        )
        self.engine.runAndWait.assert_called_once_with()

    def test_strips_text_before_speaking(self) -> None:
        self.tts.speak("  Buongiorno  ")

        self.engine.say.assert_called_once_with(
            "Buongiorno"
        )

    def test_creates_new_engine_for_each_speech(self) -> None:
        first_engine = MagicMock()
        second_engine = MagicMock()
        engine_factory = MagicMock(
            side_effect=[
                first_engine,
                second_engine,
            ]
        )

        tts = TextToSpeech(
            engine_factory=engine_factory,
            rate=170,
            volume=0.9,
        )

        tts.speak("Prima frase.")
        tts.speak("Seconda frase.")

        self.assertEqual(
            engine_factory.call_count,
            2,
        )
        first_engine.say.assert_called_once_with(
            "Prima frase."
        )
        second_engine.say.assert_called_once_with(
            "Seconda frase."
        )
        first_engine.runAndWait.assert_called_once_with()
        second_engine.runAndWait.assert_called_once_with()


    def test_rejects_empty_text(self) -> None:
        with self.assertRaises(ValueError):
            self.tts.speak("   ")

    def test_rejects_non_string_text(self) -> None:
        with self.assertRaises(TypeError):
            self.tts.speak(None)

    def test_rejects_invalid_rate(self) -> None:
        with self.assertRaises(ValueError):
            TextToSpeech(
                engine=self.engine,
                rate=0,
            )

    def test_rejects_invalid_volume(self) -> None:
        with self.assertRaises(ValueError):
            TextToSpeech(
                engine=self.engine,
                volume=1.5,
            )


if __name__ == "__main__":
    unittest.main()
