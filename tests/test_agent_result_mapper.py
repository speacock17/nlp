import unittest

from src.core.enums import (
    InconsistencyType,
    Intent,
)
from src.core.models import Inconsistency
from src.llm.agent_result_mapper import AgentResultMapper
from src.llm.ollama_llm_client import LLMToolCall
from src.llm.tool_calling_agent import (
    AgentResult,
    ToolExecution,
)


class AgentResultMapperTest(unittest.TestCase):
    def setUp(self) -> None:
        self.mapper = AgentResultMapper()

    def test_maps_artwork_list(self) -> None:
        result = AgentResult(
            content="A Napoli puoi vedere tre opere.",
            executions=[
                ToolExecution(
                    tool_call=LLMToolCall(
                        name="list_artworks_by_artist",
                        arguments={
                            "artist_name": "Caravaggio",
                            "city": "Napoli",
                        },
                    ),
                    result={
                        "count": 1,
                        "data": [
                            {
                                "uri": "artwork:1",
                                "title": (
                                    "Sette opere di Misericordia"
                                ),
                                "normalized_title": (
                                    "sette opere di misericordia"
                                ),
                                "artist_uri": "artist:1",
                                "artist_name": "Caravaggio",
                                "place_uri": "place:1",
                                "place_name": (
                                    "Pio Monte della Misericordia"
                                ),
                                "city": "Napoli",
                                "year": 1607,
                                "completion_date": None,
                                "medium": None,
                                "subject": None,
                                "description": None,
                                "image_url": None,
                                "source": "DBpedia",
                            }
                        ],
                    },
                )
            ],
        )

        response = self.mapper.map(result)

        self.assertEqual(
            response.intent,
            Intent.LIST_ARTWORKS_BY_ARTIST,
        )
        self.assertEqual(
            response.text,
            "A Napoli puoi vedere tre opere.",
        )
        self.assertEqual(len(response.artworks), 1)
        self.assertEqual(
            response.artworks[0].title,
            "Sette opere di Misericordia",
        )

    def test_uses_preferred_artwork_intent(self) -> None:
        result = AgentResult(
            content="L'opera si trova a Palazzo Zevallos.",
            executions=[
                ToolExecution(
                    tool_call=LLMToolCall(
                        name="get_artwork_information",
                        arguments={
                            "artwork_title": (
                                "Martirio di sant'Orsola"
                            )
                        },
                    ),
                    result={
                        "found": True,
                        "data": {
                            "uri": "artwork:1",
                            "title": (
                                "Martirio di sant'Orsola"
                            ),
                            "normalized_title": (
                                "martirio di sant orsola"
                            ),
                            "artist_uri": "artist:1",
                            "artist_name": "Caravaggio",
                            "place_uri": "place:1",
                            "place_name": "Palazzo Zevallos",
                            "city": "Napoli",
                            "year": 1610,
                            "completion_date": None,
                            "medium": None,
                            "subject": None,
                            "description": None,
                            "image_url": None,
                            "source": "DBpedia",
                        },
                    },
                )
            ],
        )

        response = self.mapper.map(
            result,
            preferred_intent=Intent.ARTWORK_LOCATION,
        )

        self.assertEqual(
            response.intent,
            Intent.ARTWORK_LOCATION,
        )
        self.assertEqual(
            response.artworks[0].place_name,
            "Palazzo Zevallos",
        )

    def test_infers_artwork_date_from_requested_information(
        self,
    ) -> None:
        result = AgentResult(
            content=(
                "Martirio di sant'Orsola "
                "\u00e8 stato realizzato nel 1610."
            ),
            executions=[
                ToolExecution(
                    tool_call=LLMToolCall(
                        name="get_artwork_information",
                        arguments={
                            "artwork_title": (
                                "Martirio di sant'Orsola"
                            ),
                            "requested_information": "date",
                        },
                    ),
                    result={
                        "found": True,
                        "data": {
                            "uri": "artwork:1",
                            "title": (
                                "Martirio di sant'Orsola"
                            ),
                            "normalized_title": (
                                "martirio di sant orsola"
                            ),
                            "artist_uri": "artist:1",
                            "artist_name": "Caravaggio",
                            "place_uri": "place:1",
                            "place_name": "Palazzo Zevallos",
                            "city": "Napoli",
                            "year": 1610,
                            "completion_date": None,
                            "medium": None,
                            "subject": None,
                            "description": None,
                            "image_url": None,
                            "source": "DBpedia",
                        },
                    },
                )
            ],
        )

        response = self.mapper.map(result)

        self.assertEqual(
            response.intent,
            Intent.ARTWORK_DATE,
        )

    def test_maps_artist_information(self) -> None:
        result = AgentResult(
            content="Caravaggio era un pittore italiano.",
            executions=[
                ToolExecution(
                    tool_call=LLMToolCall(
                        name="get_artist_information",
                        arguments={
                            "artist_name": "Caravaggio"
                        },
                    ),
                    result={
                        "found": True,
                        "data": {
                            "uri": "artist:1",
                            "name": "Caravaggio",
                            "normalized_name": "caravaggio",
                            "full_name": (
                                "Michelangelo Merisi"
                            ),
                            "birth_date": None,
                            "death_date": None,
                            "birth_place": None,
                            "death_place": None,
                            "description": None,
                            "image_url": None,
                            "source": "DBpedia",
                        },
                    },
                )
            ],
        )

        response = self.mapper.map(result)

        self.assertEqual(
            response.intent,
            Intent.ARTIST_INFO,
        )
        self.assertEqual(len(response.artists), 1)
        self.assertEqual(
            response.artists[0].full_name,
            "Michelangelo Merisi",
        )

    def test_preserves_inconsistency(self) -> None:
        inconsistency = Inconsistency(
            inconsistency_type=(
                InconsistencyType.WRONG_AUTHOR
            ),
            message="L'autore corretto ? Caravaggio.",
        )
        result = AgentResult(
            content="L'autore corretto ? Caravaggio.",
            executions=[],
        )

        response = self.mapper.map(
            result,
            preferred_intent=Intent.ARTWORK_AUTHOR,
            inconsistency=inconsistency,
        )

        self.assertIs(
            response.inconsistency,
            inconsistency,
        )
        self.assertEqual(
            response.intent,
            Intent.ARTWORK_AUTHOR,
        )

    def test_deduplicates_artworks_by_uri(self) -> None:
        artwork_data = {
            "uri": "artwork:1",
            "title": "Flagellazione di Cristo",
            "normalized_title": (
                "flagellazione di cristo"
            ),
            "artist_uri": "artist:1",
            "artist_name": "Caravaggio",
            "place_uri": "place:1",
            "place_name": "Museo di Capodimonte",
            "city": "Napoli",
            "year": 1607,
            "completion_date": None,
            "medium": None,
            "subject": None,
            "description": None,
            "image_url": None,
            "source": "DBpedia",
        }
        result = AgentResult(
            content="Risposta combinata.",
            executions=[
                ToolExecution(
                    tool_call=LLMToolCall(
                        name="get_artwork_information",
                        arguments={
                            "artwork_title": "Flagellazione"
                        },
                    ),
                    result={
                        "found": True,
                        "data": artwork_data,
                    },
                ),
                ToolExecution(
                    tool_call=LLMToolCall(
                        name="search_artworks",
                        arguments={
                            "query": "Flagellazione"
                        },
                    ),
                    result={
                        "count": 1,
                        "data": [artwork_data],
                    },
                ),
            ],
        )

        response = self.mapper.map(result)

        self.assertEqual(len(response.artworks), 1)


if __name__ == "__main__":
    unittest.main()
