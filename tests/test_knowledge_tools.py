import unittest
from unittest.mock import MagicMock

from src.core.models import Artist, Artwork
from src.llm.knowledge_tools import (
    KNOWLEDGE_TOOL_SCHEMAS,
    KnowledgeToolExecutor,
)


class KnowledgeToolExecutorTest(unittest.TestCase):
    def setUp(self) -> None:
        self.repository = MagicMock()
        self.executor = KnowledgeToolExecutor(
            knowledge_repository=self.repository
        )

    def test_exposes_only_expected_tools(self) -> None:
        tool_names = {
            tool["function"]["name"]
            for tool in KNOWLEDGE_TOOL_SCHEMAS
        }

        self.assertEqual(
            tool_names,
            {
                "get_artwork_information",
                "list_artworks_by_artist",
                "list_artworks_by_place",
                "get_artist_information",
                "get_place_information",
                "search_artworks",
            },
        )

    def test_gets_artwork_information(self) -> None:
        artwork = Artwork(
            uri="artwork:1",
            title="Martirio di sant'Orsola",
            normalized_title="martirio di sant orsola",
            artist_uri="artist:1",
            artist_name="Caravaggio",
            place_name="Palazzo Zevallos",
            city="Napoli",
            year=1610,
        )
        self.repository.get_artwork_by_title.return_value = (
            artwork
        )

        result = self.executor.execute(
            name="get_artwork_information",
            arguments={
                "artwork_title": (
                    "Martirio di sant'Orsola"
                )
            },
        )

        self.repository.get_artwork_by_title.assert_called_once_with(
            "Martirio di sant'Orsola"
        )
        self.assertTrue(result["found"])
        self.assertEqual(
            result["data"]["artist_name"],
            "Caravaggio",
        )
        self.assertEqual(
            result["data"]["place_name"],
            "Palazzo Zevallos",
        )

    def test_lists_artworks_by_artist(self) -> None:
        artwork = Artwork(
            uri="artwork:1",
            title="Sette opere di Misericordia",
            normalized_title=(
                "sette opere di misericordia"
            ),
            artist_uri="artist:1",
            artist_name="Caravaggio",
            city="Napoli",
        )
        self.repository.list_artworks_by_artist.return_value = [
            artwork
        ]

        result = self.executor.execute(
            name="list_artworks_by_artist",
            arguments={
                "artist_name": "Caravaggio",
                "city": "Napoli",
            },
        )

        self.repository.list_artworks_by_artist.assert_called_once_with(
            "Caravaggio",
            "Napoli",
        )
        self.assertEqual(result["count"], 1)
        self.assertEqual(
            result["data"][0]["title"],
            "Sette opere di Misericordia",
        )

    def test_gets_artist_information(self) -> None:
        artist = Artist(
            uri="artist:1",
            name="Caravaggio",
            normalized_name="caravaggio",
            full_name="Michelangelo Merisi",
        )
        self.repository.get_artist_by_name.return_value = artist

        result = self.executor.execute(
            name="get_artist_information",
            arguments={"artist_name": "Caravaggio"},
        )

        self.assertTrue(result["found"])
        self.assertEqual(
            result["data"]["full_name"],
            "Michelangelo Merisi",
        )

    def test_returns_not_found(self) -> None:
        self.repository.get_artwork_by_title.return_value = None

        result = self.executor.execute(
            name="get_artwork_information",
            arguments={"artwork_title": "Opera inesistente"},
        )

        self.assertEqual(
            result,
            {
                "found": False,
                "data": None,
            },
        )

    def test_rejects_unknown_tool(self) -> None:
        with self.assertRaises(ValueError):
            self.executor.execute(
                name="delete_database",
                arguments={},
            )


if __name__ == "__main__":
    unittest.main()
