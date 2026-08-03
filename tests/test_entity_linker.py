import unittest

from src.core.enums import EntityType
from src.database.mock_knowledge_repository import (
    MockKnowledgeRepository,
)
from src.nlp.entity_linker import EntityLinker


class EntityLinkerTest(unittest.TestCase):
    def setUp(self) -> None:
        self.linker = EntityLinker(
            MockKnowledgeRepository()
        )

    def test_links_exact_artist(self) -> None:
        entities = self.linker.link(
            "Quali opere di Caravaggio posso vedere?"
        )

        self.assertEqual(len(entities), 1)
        self.assertEqual(
            entities[0].entity_type,
            EntityType.ARTIST,
        )
        self.assertEqual(
            entities[0].canonical_name,
            "Caravaggio",
        )
        self.assertEqual(
            entities[0].uri,
            "http://dbpedia.org/resource/Caravaggio",
        )
        self.assertEqual(entities[0].confidence, 1.0)

    def test_links_artist_with_typo(self) -> None:
        entities = self.linker.link(
            "Parlami di Caravagio"
        )

        self.assertEqual(len(entities), 1)
        self.assertEqual(
            entities[0].canonical_name,
            "Caravaggio",
        )
        self.assertGreaterEqual(
            entities[0].confidence,
            0.90,
        )

    def test_links_battistello_alias(self) -> None:
        entities = self.linker.link(
            "Quali opere ha realizzato Battistello?"
        )

        self.assertEqual(len(entities), 1)
        self.assertEqual(
            entities[0].canonical_name,
            "Battistello Caracciolo",
        )

    def test_links_exact_artwork(self) -> None:
        entities = self.linker.link(
            "Dove si trova il Martirio di sant'Orsola?"
        )

        artworks = [
            entity
            for entity in entities
            if entity.entity_type == EntityType.ARTWORK
        ]

        self.assertEqual(len(artworks), 1)
        self.assertEqual(
            artworks[0].canonical_name,
            "Martirio di sant'Orsola",
        )

    def test_links_artwork_without_parenthetical_artist(
        self,
    ) -> None:
        entities = self.linker.link(
            "Descrivi la Flagellazione di Cristo"
        )

        artworks = [
            entity
            for entity in entities
            if entity.entity_type == EntityType.ARTWORK
        ]

        self.assertEqual(len(artworks), 1)
        self.assertEqual(
            artworks[0].canonical_name,
            "Flagellazione di Cristo (Caravaggio)",
        )

    def test_links_place_alias(self) -> None:
        entities = self.linker.link(
            "Quali opere sono conservate a Capodimonte?"
        )

        places = [
            entity
            for entity in entities
            if entity.entity_type == EntityType.PLACE
        ]

        self.assertEqual(len(places), 1)
        self.assertEqual(
            places[0].canonical_name,
            "Museo nazionale di Capodimonte",
        )

    def test_links_multiple_artists(self) -> None:
        entities = self.linker.link(
            "Confronta Caravaggio e Battistello Caracciolo"
        )

        artists = [
            entity.canonical_name
            for entity in entities
            if entity.entity_type == EntityType.ARTIST
        ]

        self.assertEqual(
            artists,
            [
                "Caravaggio",
                "Battistello Caracciolo",
            ],
        )

    def test_links_city(self) -> None:
        entities = self.linker.link(
            "Quali opere posso vedere a Napoli?"
        )

        cities = [
            entity
            for entity in entities
            if entity.entity_type == EntityType.CITY
        ]

        self.assertEqual(len(cities), 1)
        self.assertEqual(
            cities[0].canonical_name,
            "Napoli",
        )
        self.assertIsNone(cities[0].uri)

    def test_unrelated_text_returns_empty_list(self) -> None:
        self.assertEqual(
            self.linker.link("Che tempo fa domani?"),
            [],
        )

    def test_empty_text_returns_empty_list(self) -> None:
        self.assertEqual(
            self.linker.link(""),
            [],
        )


if __name__ == "__main__":
    unittest.main()
