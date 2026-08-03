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


if __name__ == "__main__":
    unittest.main()
