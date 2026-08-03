import unittest

from src.core.enums import Intent
from src.nlp.intent_classifier import classify_intent


class IntentClassifierTest(unittest.TestCase):
    def assert_intent(
        self,
        text: str,
        expected: Intent,
    ) -> None:
        intent, confidence = classify_intent(text)

        self.assertEqual(intent, expected)
        self.assertGreaterEqual(confidence, 0.0)
        self.assertLessEqual(confidence, 1.0)

    def test_list_artworks_by_artist(self) -> None:
        self.assert_intent(
            "quali opere di caravaggio posso vedere a napoli",
            Intent.LIST_ARTWORKS_BY_ARTIST,
        )

    def test_artwork_location(self) -> None:
        self.assert_intent(
            "dove si trova il martirio di sant orsola",
            Intent.ARTWORK_LOCATION,
        )

    def test_artwork_location_follow_up_variants(self) -> None:
        questions = (
            "Dov'è situata?",
            "Dov'è situato?",
            "Dov'è conservata?",
            "Dov'è conservato?",
        )

        for question in questions:
            with self.subTest(question=question):
                self.assert_intent(
                    question,
                    Intent.ARTWORK_LOCATION,
                )

    def test_artwork_author(self) -> None:
        self.assert_intent(
            "chi ha dipinto la flagellazione di cristo",
            Intent.ARTWORK_AUTHOR,
        )

    def test_artwork_date(self) -> None:
        self.assert_intent(
            "in che anno e stata dipinta quest opera",
            Intent.ARTWORK_DATE,
        )

    def test_artwork_description(self) -> None:
        self.assert_intent(
            "descrivimi le sette opere di misericordia",
            Intent.ARTWORK_DESCRIPTION,
        )

    def test_artist_info(self) -> None:
        self.assert_intent(
            "chi era battistello caracciolo",
            Intent.ARTIST_INFO,
        )

    def test_place_artworks(self) -> None:
        self.assert_intent(
            "quali opere si trovano al museo di capodimonte",
            Intent.PLACE_ARTWORKS,
        )

    def test_compare_artists(self) -> None:
        self.assert_intent(
            "confronta caravaggio e battistello caracciolo",
            Intent.COMPARE_ARTISTS,
        )

    def test_follow_up(self) -> None:
        self.assert_intent(
            "e le altre",
            Intent.FOLLOW_UP,
        )

    def test_out_of_scope(self) -> None:
        self.assert_intent(
            "che tempo fa domani",
            Intent.OUT_OF_SCOPE,
        )

    def test_unknown(self) -> None:
        self.assert_intent(
            "ciao",
            Intent.UNKNOWN,
        )

    def test_empty_text_is_unknown(self) -> None:
        self.assert_intent(
            "",
            Intent.UNKNOWN,
        )


if __name__ == "__main__":
    unittest.main()
