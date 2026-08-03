import unittest

from src.core.enums import (
    InconsistencyType,
    Intent,
)
from src.core.models import (
    Inconsistency,
    NLUResult,
)
from src.database.mock_knowledge_repository import (
    MockKnowledgeRepository,
)
from src.dialogue.response_generator import (
    ResponseGenerator,
)
from src.nlp.nlu_pipeline import NLUPipeline


class ResponseGeneratorTest(unittest.TestCase):
    def setUp(self) -> None:
        self.repository = MockKnowledgeRepository()
        self.pipeline = NLUPipeline(self.repository)
        self.generator = ResponseGenerator(
            self.repository
        )

    def _generate(self, text: str):
        nlu_result = self.pipeline.analyze(text)

        return self.generator.generate(
            nlu_result
        )

    def test_lists_artworks_by_artist(self) -> None:
        response = self._generate(
            "Quali opere di Caravaggio posso vedere a Napoli?"
        )

        self.assertEqual(
            response.intent,
            Intent.LIST_ARTWORKS_BY_ARTIST,
        )
        self.assertEqual(len(response.artworks), 3)
        self.assertIn("Caravaggio", response.text)
        self.assertIn(
            "Martirio di sant'Orsola",
            response.text,
        )

    def test_returns_artwork_location(self) -> None:
        response = self._generate(
            "Dove si trova il Martirio di sant'Orsola?"
        )

        self.assertEqual(
            response.intent,
            Intent.ARTWORK_LOCATION,
        )
        self.assertEqual(len(response.artworks), 1)
        self.assertIn(
            "Palazzo Zevallos",
            response.text,
        )

    def test_returns_artwork_author(self) -> None:
        response = self._generate(
            "Chi ha dipinto il Martirio di sant'Orsola?"
        )

        self.assertEqual(
            response.intent,
            Intent.ARTWORK_AUTHOR,
        )
        self.assertIn(
            "Caravaggio",
            response.text,
        )

    def test_returns_artwork_date(self) -> None:
        response = self._generate(
            "In che anno è stato dipinto "
            "il Martirio di sant'Orsola?"
        )

        self.assertEqual(
            response.intent,
            Intent.ARTWORK_DATE,
        )
        self.assertIn("1610", response.text)

    def test_returns_artwork_description(self) -> None:
        response = self._generate(
            "Descrivimi le Sette opere di Misericordia"
        )

        self.assertEqual(
            response.intent,
            Intent.ARTWORK_DESCRIPTION,
        )
        self.assertEqual(len(response.artworks), 1)
        self.assertTrue(response.text)

    def test_compares_two_artists(self) -> None:
        response = self._generate(
            "Confronta Caravaggio e Battistello Caracciolo"
        )

        self.assertEqual(
            response.intent,
            Intent.COMPARE_ARTISTS,
        )
        self.assertEqual(len(response.artists), 2)
        self.assertEqual(len(response.artworks), 11)
        self.assertIn(
            "Caravaggio ha 3 opere",
            response.text,
        )
        self.assertIn(
            "Battistello Caracciolo ne ha 8",
            response.text,
        )
        self.assertFalse(
            response.needs_clarification
        )

    def test_compare_artists_requires_two_artists(
        self,
    ) -> None:
        response = self._generate(
            "Confronta Caravaggio"
        )

        self.assertEqual(
            response.intent,
            Intent.COMPARE_ARTISTS,
        )
        self.assertTrue(
            response.needs_clarification
        )
        self.assertIn(
            "Quali due artisti",
            response.text,
        )

    def test_returns_inconsistency_message(self) -> None:
        nlu_result = self.pipeline.analyze(
            "Il Martirio di sant'Orsola è di "
            "Battistello Caracciolo?"
        )
        inconsistency = Inconsistency(
            inconsistency_type=(
                InconsistencyType.WRONG_AUTHOR
            ),
            message=(
                "L'autore indicato non è corretto: "
                "Martirio di sant'Orsola è attribuita "
                "a Caravaggio."
            ),
            claimed_value="Battistello Caracciolo",
            correct_value="Caravaggio",
        )

        response = self.generator.generate(
            nlu_result,
            inconsistency=inconsistency,
        )

        self.assertEqual(
            response.inconsistency,
            inconsistency,
        )
        self.assertEqual(
            response.text,
            inconsistency.message,
        )

    def test_out_of_scope_response(self) -> None:
        response = self._generate(
            "Che tempo fa domani?"
        )

        self.assertEqual(
            response.intent,
            Intent.OUT_OF_SCOPE,
        )
        self.assertIn(
            "Caravaggio",
            response.text,
        )

    def test_unknown_response(self) -> None:
        result = NLUResult(
            raw_text="ciao",
            normalized_text="ciao",
            intent=Intent.UNKNOWN,
            intent_confidence=0.20,
        )

        response = self.generator.generate(result)

        self.assertEqual(
            response.intent,
            Intent.UNKNOWN,
        )
        self.assertTrue(
            response.needs_clarification
        )


if __name__ == "__main__":
    unittest.main()
