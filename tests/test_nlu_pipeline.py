import unittest

from src.core.enums import (
    ClaimType,
    EntityType,
    Intent,
)
from src.core.models import NLUResult
from src.database.mock_knowledge_repository import (
    MockKnowledgeRepository,
)
from src.nlp.nlu_pipeline import NLUPipeline


class NLUPipelineTest(unittest.TestCase):
    def setUp(self) -> None:
        self.pipeline = NLUPipeline(
            MockKnowledgeRepository()
        )

    def test_returns_shared_nlu_result(self) -> None:
        result = self.pipeline.analyze(
            "Dove si trova il Martirio di sant'Orsola?"
        )

        self.assertIsInstance(result, NLUResult)
        self.assertEqual(
            result.raw_text,
            "Dove si trova il Martirio di sant'Orsola?",
        )
        self.assertEqual(
            result.normalized_text,
            "dove si trova il martirio di sant orsola",
        )
        self.assertEqual(
            result.intent,
            Intent.ARTWORK_LOCATION,
        )
        self.assertGreaterEqual(
            result.intent_confidence,
            0.0,
        )
        self.assertLessEqual(
            result.intent_confidence,
            1.0,
        )

    def test_includes_linked_entities(self) -> None:
        result = self.pipeline.analyze(
            "Parlami di Caravagio"
        )

        self.assertEqual(
            result.intent,
            Intent.ARTIST_INFO,
        )
        self.assertEqual(len(result.entities), 1)
        self.assertEqual(
            result.entities[0].entity_type,
            EntityType.ARTIST,
        )
        self.assertEqual(
            result.entities[0].canonical_name,
            "Caravaggio",
        )

    def test_includes_author_claim(self) -> None:
        result = self.pipeline.analyze(
            "Il Martirio di sant'Orsola è di "
            "Battistello Caracciolo?"
        )

        self.assertEqual(len(result.claims), 1)
        self.assertEqual(
            result.claims[0].claim_type,
            ClaimType.ARTWORK_AUTHOR,
        )
        self.assertEqual(
            result.claims[0].claimed_value,
            "Battistello Caracciolo",
        )

    def test_information_request_has_no_claim(self) -> None:
        result = self.pipeline.analyze(
            "Chi ha dipinto il Martirio di sant'Orsola?"
        )

        self.assertEqual(
            result.intent,
            Intent.ARTWORK_AUTHOR,
        )
        self.assertEqual(result.claims, [])

    def test_multiple_entities_are_preserved(self) -> None:
        result = self.pipeline.analyze(
            "Confronta Caravaggio e Battistello Caracciolo"
        )

        artists = [
            entity
            for entity in result.entities
            if entity.entity_type == EntityType.ARTIST
        ]

        self.assertEqual(
            result.intent,
            Intent.COMPARE_ARTISTS,
        )
        self.assertEqual(len(artists), 2)

    def test_recognizes_ordinal_references(
        self,
    ) -> None:
        cases = [
            (
                "Dove si trova il primo elencato?",
                "1",
            ),
            (
                "Dove si trova il secondo elencato?",
                "2",
            ),
            (
                "Dove si trova il terzo elencato?",
                "3",
            ),
            (
                "Dove si trova l'ultimo elencato?",
                "last",
            ),
        ]

        for text, expected_value in cases:
            with self.subTest(text=text):
                result = self.pipeline.analyze(text)

                ordinal_entities = [
                    entity
                    for entity in result.entities
                    if entity.entity_type
                    == EntityType.ORDINAL
                ]

                self.assertEqual(
                    result.intent,
                    Intent.ARTWORK_LOCATION,
                )
                self.assertEqual(
                    len(ordinal_entities),
                    1,
                )
                self.assertEqual(
                    ordinal_entities[0].canonical_name,
                    expected_value,
                )
                self.assertIsNone(
                    ordinal_entities[0].uri,
                )

    def test_out_of_scope_question(self) -> None:
        result = self.pipeline.analyze(
            "Che tempo fa domani?"
        )

        self.assertEqual(
            result.intent,
            Intent.OUT_OF_SCOPE,
        )
        self.assertEqual(result.entities, [])
        self.assertEqual(result.claims, [])

    def test_empty_text(self) -> None:
        result = self.pipeline.analyze("")

        self.assertEqual(
            result.intent,
            Intent.UNKNOWN,
        )
        self.assertEqual(result.normalized_text, "")
        self.assertEqual(result.entities, [])
        self.assertEqual(result.claims, [])


if __name__ == "__main__":
    unittest.main()
