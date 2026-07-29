import unittest

from src.nlp.fuzzy_matching import (
    fuzzy_similarity,
    is_accepted_match,
    is_ambiguous_match,
)


class FuzzyMatchingTest(unittest.TestCase):
    def test_exact_match(self) -> None:
        self.assertEqual(
            fuzzy_similarity(
                "Caravaggio",
                "Caravaggio",
            ),
            1.0,
        )

    def test_normalization_is_applied(self) -> None:
        self.assertEqual(
            fuzzy_similarity(
                "Martirio di sant’Orsola",
                "martirio di sant orsola",
            ),
            1.0,
        )

    def test_small_typo_is_accepted(self) -> None:
        score = fuzzy_similarity(
            "caravagio",
            "caravaggio",
        )

        self.assertTrue(is_accepted_match(score))

    def test_contained_alias_is_accepted(self) -> None:
        score = fuzzy_similarity(
            "capodimonte",
            "Museo nazionale di Capodimonte",
        )

        self.assertEqual(score, 1.0)
        self.assertTrue(is_accepted_match(score))

    def test_ambiguous_score(self) -> None:
        self.assertTrue(
            is_ambiguous_match(0.80)
        )
        self.assertFalse(
            is_accepted_match(0.80)
        )

    def test_accepted_boundary(self) -> None:
        self.assertTrue(
            is_accepted_match(0.90)
        )
        self.assertFalse(
            is_ambiguous_match(0.90)
        )

    def test_ambiguous_boundary(self) -> None:
        self.assertTrue(
            is_ambiguous_match(0.75)
        )

    def test_rejected_score(self) -> None:
        self.assertFalse(
            is_accepted_match(0.50)
        )
        self.assertFalse(
            is_ambiguous_match(0.50)
        )

    def test_empty_text_has_zero_similarity(self) -> None:
        self.assertEqual(
            fuzzy_similarity("", "Caravaggio"),
            0.0,
        )
        self.assertEqual(
            fuzzy_similarity("Caravaggio", ""),
            0.0,
        )

    def test_unrelated_text_is_not_accepted(self) -> None:
        score = fuzzy_similarity(
            "calcio",
            "Caravaggio",
        )

        self.assertFalse(
            is_accepted_match(score)
        )


if __name__ == "__main__":
    unittest.main()
