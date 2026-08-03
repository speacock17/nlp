import unittest
from unittest.mock import MagicMock

from src.gui.speech_to_text_cache import (
    SpeechToTextCache,
)


class SpeechToTextCacheTest(unittest.TestCase):
    def setUp(self) -> None:
        self.factory = MagicMock()
        self.initial_engine = MagicMock()

        self.cache = SpeechToTextCache(
            factory=self.factory,
            initial_engine_name="whisper",
            initial_engine=self.initial_engine,
        )

    def test_reuses_initial_engine(self) -> None:
        result = self.cache.get("  WHISPER  ")

        self.assertIs(result, self.initial_engine)
        self.factory.assert_not_called()

    def test_creates_engine_only_once(self) -> None:
        google_engine = MagicMock()
        self.factory.return_value = google_engine

        first_result = self.cache.get("google")
        second_result = self.cache.get("GOOGLE")

        self.assertIs(first_result, google_engine)
        self.assertIs(second_result, google_engine)
        self.factory.assert_called_once_with("google")

    def test_rejects_empty_engine_name(self) -> None:
        with self.assertRaises(ValueError):
            self.cache.get("   ")


if __name__ == "__main__":
    unittest.main()
