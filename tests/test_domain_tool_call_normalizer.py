import unittest

from src.llm.domain_tool_call_normalizer import (
    DomainToolCallNormalizer,
)
from src.llm.ollama_llm_client import LLMToolCall


class DomainToolCallNormalizerTest(unittest.TestCase):
    def setUp(self) -> None:
        self.normalizer = DomainToolCallNormalizer()

    def test_converts_merisi_to_caravaggio(
        self,
    ) -> None:
        tool_call = LLMToolCall(
            name="list_artworks_by_artist",
            arguments={
                "artist_name": "Merisi",
                "city": "Napoli",
            },
        )

        result = self.normalizer.normalize(
            user_text=(
                "Vorrei vedere qualche quadro "
                "del Merisi a Napoli."
            ),
            tool_call=tool_call,
        )

        self.assertEqual(
            result,
            LLMToolCall(
                name="list_artworks_by_artist",
                arguments={
                    "artist_name": "Caravaggio",
                    "city": "Napoli",
                },
            ),
        )

    def test_converts_full_name_to_caravaggio(
        self,
    ) -> None:
        tool_call = LLMToolCall(
            name="get_artist_information",
            arguments={
                "artist_name": "Michelangelo Merisi"
            },
        )

        result = self.normalizer.normalize(
            user_text=(
                "Parlami di Michelangelo Merisi."
            ),
            tool_call=tool_call,
        )

        self.assertEqual(
            result.arguments["artist_name"],
            "Caravaggio",
        )

    def test_repairs_naples_place_call_for_merisi(
        self,
    ) -> None:
        tool_call = LLMToolCall(
            name="list_artworks_by_place",
            arguments={
                "place_name": "Napoli"
            },
        )

        result = self.normalizer.normalize(
            user_text=(
                "Vorrei fare un giro per Napoli "
                "e vedere qualche quadro del Merisi."
            ),
            tool_call=tool_call,
        )

        self.assertEqual(
            result,
            LLMToolCall(
                name="list_artworks_by_artist",
                arguments={
                    "artist_name": "Caravaggio",
                    "city": "Napoli",
                },
            ),
        )

    def test_preserves_real_place_request(
        self,
    ) -> None:
        tool_call = LLMToolCall(
            name="list_artworks_by_place",
            arguments={
                "place_name": (
                    "Pio Monte della Misericordia"
                )
            },
        )

        result = self.normalizer.normalize(
            user_text=(
                "Quali opere posso vedere al "
                "Pio Monte della Misericordia?"
            ),
            tool_call=tool_call,
        )

        self.assertEqual(result, tool_call)

    def test_preserves_battistello_caracciolo(
        self,
    ) -> None:
        tool_call = LLMToolCall(
            name="list_artworks_by_artist",
            arguments={
                "artist_name": (
                    "Battistello Caracciolo"
                ),
                "city": "Napoli",
            },
        )

        result = self.normalizer.normalize(
            user_text=(
                "Quali opere di Battistello "
                "Caracciolo vedo a Napoli?"
            ),
            tool_call=tool_call,
        )

        self.assertEqual(result, tool_call)


    def test_keeps_only_overview_for_artist_information(
        self,
    ) -> None:
        tool_call = LLMToolCall(
            name="get_artist_information",
            arguments={
                "artist_name": "Battistello Caracciolo",
                "requested_fields": [
                    "overview",
                    "full_name",
                    "birth_date",
                    "birth_place",
                    "death_date",
                    "death_place",
                    "description",
                ],
            },
        )

        result = self.normalizer.normalize(
            user_text=(
                "Parlami di Battistello Caracciolo."
            ),
            tool_call=tool_call,
        )

        self.assertEqual(
            result.arguments["requested_fields"],
            ["overview"],
        )
        self.assertEqual(
            result.arguments["artist_name"],
            "Battistello Caracciolo",
        )

    def test_keeps_only_overview_for_artwork_information(
        self,
    ) -> None:
        tool_call = LLMToolCall(
            name="get_artwork_information",
            arguments={
                "artwork_title": (
                    "Flagellazione di Cristo"
                ),
                "requested_fields": [
                    "overview",
                    "author",
                    "date",
                    "medium",
                    "location",
                ],
            },
        )

        result = self.normalizer.normalize(
            user_text=(
                "Parlami della Flagellazione di Cristo."
            ),
            tool_call=tool_call,
        )

        self.assertEqual(
            result.arguments["requested_fields"],
            ["overview"],
        )
        self.assertEqual(
            result.arguments["artwork_title"],
            "Flagellazione di Cristo",
        )



if __name__ == "__main__":
    unittest.main()
