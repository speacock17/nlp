import unittest

from neo4j.exceptions import Neo4jError

from src.core.interfaces import KnowledgeRepository
from src.core.models import Artist, Artwork, Place
from src.database.neo4j_knowledge_repository import (
    Neo4jKnowledgeRepository,
)


class Neo4jKnowledgeRepositoryIntegrationTest(
    unittest.TestCase
):
    repository: Neo4jKnowledgeRepository

    @classmethod
    def setUpClass(cls) -> None:
        try:
            cls.repository = (
                Neo4jKnowledgeRepository.from_env()
            )

            if not cls.repository.check_health():
                cls.repository.close()
                raise unittest.SkipTest(
                    "Neo4j non disponibile"
                )
        except (RuntimeError, Neo4jError) as error:
            raise unittest.SkipTest(
                f"Neo4j non disponibile: {error}"
            ) from error

    @classmethod
    def tearDownClass(cls) -> None:
        repository = getattr(cls, "repository", None)

        if repository is not None:
            repository.close()

    def test_implements_shared_interface(self) -> None:
        self.assertIsInstance(
            self.repository,
            KnowledgeRepository,
        )

    def test_health(self) -> None:
        self.assertTrue(
            self.repository.check_health()
        )

    def test_get_artwork_by_uri(self) -> None:
        artwork = self.repository.get_artwork_by_uri(
            "http://dbpedia.org/resource/"
            "The_Martyrdom_of_Saint_Ursula_"
            "(Caravaggio)"
        )

        self.assertIsInstance(artwork, Artwork)
        self.assertEqual(
            artwork.title,
            "Martirio di sant'Orsola",
        )

    def test_get_artwork_by_title(self) -> None:
        artwork = self.repository.get_artwork_by_title(
            "Martirio di sant'Orsola"
        )

        self.assertIsInstance(artwork, Artwork)
        self.assertEqual(artwork.year, 1610)

    def test_get_missing_artwork(self) -> None:
        self.assertIsNone(
            self.repository.get_artwork_by_uri(
                "urn:artwork:not-found"
            )
        )
        self.assertIsNone(
            self.repository.get_artwork_by_title("")
        )

    def test_search_artworks(self) -> None:
        artworks = self.repository.search_artworks(
            "misericordia",
            limit=5,
        )

        self.assertEqual(len(artworks), 1)
        self.assertEqual(
            artworks[0].title,
            "Sette opere di Misericordia",
        )

    def test_list_artworks_by_artist(self) -> None:
        caravaggio = (
            self.repository.list_artworks_by_artist(
                "Caravaggio"
            )
        )
        battistello = (
            self.repository.list_artworks_by_artist(
                "Battistello Caracciolo"
            )
        )

        self.assertEqual(len(caravaggio), 3)
        self.assertEqual(len(battistello), 8)
        self.assertTrue(
            all(
                isinstance(item, Artwork)
                for item in caravaggio + battistello
            )
        )

    def test_list_artworks_by_place(self) -> None:
        artworks = (
            self.repository.list_artworks_by_place(
                "Museo nazionale di Capodimonte"
            )
        )

        self.assertEqual(len(artworks), 4)
        self.assertTrue(
            all(
                item.place_name
                == "Museo nazionale di Capodimonte"
                for item in artworks
            )
        )

    def test_get_artist(self) -> None:
        by_name = self.repository.get_artist_by_name(
            "Caravaggio"
        )
        by_uri = self.repository.get_artist_by_uri(
            "http://dbpedia.org/resource/Caravaggio"
        )

        self.assertIsInstance(by_name, Artist)
        self.assertIsInstance(by_uri, Artist)
        self.assertEqual(by_name, by_uri)

    def test_search_artists(self) -> None:
        artists = self.repository.search_artists(
            "caracciolo",
            limit=5,
        )

        self.assertEqual(len(artists), 1)
        self.assertEqual(
            artists[0].name,
            "Battistello Caracciolo",
        )

    def test_get_place_by_name(self) -> None:
        place = self.repository.get_place_by_name(
            "Pio Monte della Misericordia"
        )

        self.assertIsInstance(place, Place)
        self.assertEqual(
            place.address,
            "Via dei Tribunali, 253",
        )
        self.assertEqual(
            place.uri,
            "http://dbpedia.org/resource/"
            "Pio_Monte_della_Misericordia",
        )

    def test_search_places(self) -> None:
        places = self.repository.search_places(
            "palazzo",
            limit=5,
        )

        self.assertEqual(len(places), 2)
        self.assertEqual(
            {place.name for place in places},
            {
                "Palazzo Reale di Napoli",
                "Palazzo Zevallos",
            },
        )

    def test_invalid_search_limit(self) -> None:
        with self.assertRaises(ValueError):
            self.repository.search_artworks(
                "opera",
                limit=0,
            )

        with self.assertRaises(ValueError):
            self.repository.search_artists(
                "artista",
                limit=0,
            )

        with self.assertRaises(ValueError):
            self.repository.search_places(
                "luogo",
                limit=0,
            )


if __name__ == "__main__":
    unittest.main()
