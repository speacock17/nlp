import unittest

from src.core.enums import (
    ClaimType,
    EntityType,
)
from src.core.models import EntityMention
from src.database.mock_knowledge_repository import (
    MockKnowledgeRepository,
)
from src.nlp.claim_extractor import ClaimExtractor
from src.nlp.entity_linker import EntityLinker


class ClaimExtractorTest(unittest.TestCase):
    def setUp(self) -> None:
        repository = MockKnowledgeRepository()
        self.linker = EntityLinker(repository)
        self.extractor = ClaimExtractor()

    def _extract(self, text: str):
        entities = self.linker.link(text)

        return self.extractor.extract(
            text,
            entities,
        )

    def test_extracts_author_claim(self) -> None:
        claims = self._extract(
            "Il Martirio di sant'Orsola è di "
            "Battistello Caracciolo?"
        )

        self.assertEqual(len(claims), 1)
        self.assertEqual(
            claims[0].claim_type,
            ClaimType.ARTWORK_AUTHOR,
        )
        self.assertEqual(
            claims[0].claimed_value,
            "Battistello Caracciolo",
        )
        self.assertEqual(
            claims[0].subject_uri,
            "http://dbpedia.org/resource/"
            "The_Martyrdom_of_Saint_Ursula_"
            "(Caravaggio)",
        )

    def test_extracts_location_claim(self) -> None:
        claims = self._extract(
            "Il Martirio di sant'Orsola si trova "
            "a Capodimonte?"
        )

        self.assertEqual(len(claims), 1)
        self.assertEqual(
            claims[0].claim_type,
            ClaimType.ARTWORK_LOCATION,
        )
        self.assertEqual(
            claims[0].claimed_value,
            "Museo nazionale di Capodimonte",
        )

    def test_extracts_plural_location_claim(
        self,
    ) -> None:
        claims = self._extract(
            "Le Sette opere di Misericordia si trovano "
            "al Museo di Capodimonte?"
        )

        self.assertEqual(len(claims), 1)
        self.assertEqual(
            claims[0].claim_type,
            ClaimType.ARTWORK_LOCATION,
        )
        self.assertEqual(
            claims[0].claimed_value,
            "Museo nazionale di Capodimonte",
        )

    def test_extracts_date_claim(self) -> None:
        claims = self._extract(
            "Il Martirio di sant'Orsola è del 1607?"
        )

        self.assertEqual(len(claims), 1)
        self.assertEqual(
            claims[0].claim_type,
            ClaimType.ARTWORK_DATE,
        )
        self.assertEqual(
            claims[0].claimed_value,
            "1607",
        )

    def test_correct_author_is_also_a_claim(self) -> None:
        claims = self._extract(
            "Il Martirio di sant'Orsola è di Caravaggio?"
        )

        self.assertEqual(len(claims), 1)
        self.assertEqual(
            claims[0].claimed_value,
            "Caravaggio",
        )

    def test_extracts_author_claim_from_generic_relation(
        self,
    ) -> None:
        entities = [
            EntityMention(
                entity_type=EntityType.ARTWORK,
                text="Opera di prova",
                canonical_name="Opera di prova",
                uri="artwork:test",
                confidence=1.0,
            ),
            EntityMention(
                entity_type=EntityType.ARTIST,
                text="Artista di prova",
                canonical_name="Artista di prova",
                uri="artist:test",
                confidence=1.0,
            ),
        ]

        claims = self.extractor.extract(
            (
                "Quando \u00e8 stata realizzata "
                "Opera di prova di Artista di prova?"
            ),
            entities,
        )

        self.assertEqual(len(claims), 1)
        self.assertEqual(
            claims[0].claim_type,
            ClaimType.ARTWORK_AUTHOR,
        )
        self.assertEqual(
            claims[0].subject_uri,
            "artwork:test",
        )
        self.assertEqual(
            claims[0].claimed_value,
            "Artista di prova",
        )

    def test_question_without_artwork_has_no_claim(
        self,
    ) -> None:
        claims = self._extract(
            "Battistello Caracciolo è un pittore?"
        )

        self.assertEqual(claims, [])

    def test_information_request_has_no_claim(self) -> None:
        claims = self._extract(
            "Chi ha dipinto il Martirio di sant'Orsola?"
        )

        self.assertEqual(claims, [])

    def test_empty_text_has_no_claim(self) -> None:
        self.assertEqual(
            self._extract(""),
            [],
        )


if __name__ == "__main__":
    unittest.main()
