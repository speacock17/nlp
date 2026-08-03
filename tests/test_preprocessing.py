import unittest

from src.nlp.preprocessing import preprocess_question


class PreprocessingTest(unittest.TestCase):
    def test_normalizes_question(self) -> None:
        result = preprocess_question(
            "  Dov'è la Flagellazione di Cristo?  "
        )

        self.assertEqual(
            result,
            "dov e la flagellazione di cristo",
        )

    def test_normalizes_accents_and_apostrophes(self) -> None:
        result = preprocess_question(
            "Qual è l’autore dell’opera?"
        )

        self.assertEqual(
            result,
            "qual e l autore dell opera",
        )

    def test_collapses_spaces(self) -> None:
        result = preprocess_question(
            "Caravaggio     a    Napoli"
        )

        self.assertEqual(
            result,
            "caravaggio a napoli",
        )

    def test_empty_string_returns_empty_string(self) -> None:
        self.assertEqual(
            preprocess_question(""),
            "",
        )

    def test_only_punctuation_returns_empty_string(
        self,
    ) -> None:
        self.assertEqual(
            preprocess_question("?!.,"),
            "",
        )

    def test_non_string_raises_type_error(self) -> None:
        with self.assertRaises(TypeError):
            preprocess_question(None)  # type: ignore[arg-type]


if __name__ == "__main__":
    unittest.main()
