import unittest

from src.core.normalization import normalize_text


class NormalizeTextTest(unittest.TestCase):
    def test_accents_and_apostrophe(self) -> None:
        self.assertEqual(
            normalize_text("L’Incredulità di San Tommaso"),
            "l incredulita di san tommaso",
        )

    def test_punctuation_and_extra_spaces(self) -> None:
        self.assertEqual(
            normalize_text("  Caravaggio: Napoli!  "),
            "caravaggio napoli",
        )

    def test_casefold(self) -> None:
        self.assertEqual(
            normalize_text("BATTISTELLO Caracciolo"),
            "battistello caracciolo",
        )

    def test_empty_string(self) -> None:
        self.assertEqual(normalize_text(""), "")


if __name__ == "__main__":
    unittest.main()
