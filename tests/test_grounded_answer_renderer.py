import unittest

from src.llm.grounded_answer_renderer import (
    GroundedAnswerRenderer,
)
from src.llm.ollama_llm_client import LLMToolCall
from src.llm.tool_calling_agent import ToolExecution


class GroundedAnswerRendererTest(unittest.TestCase):
    def setUp(self) -> None:
        self.renderer = GroundedAnswerRenderer()

    def test_renders_artworks_with_their_real_places(
        self,
    ) -> None:
        execution = ToolExecution(
            tool_call=LLMToolCall(
                name="list_artworks_by_artist",
                arguments={
                    "artist_name": "Caravaggio",
                    "city": "Napoli",
                },
            ),
            result={
                "count": 3,
                "data": [
                    {
                        "title": "Flagellazione di Cristo",
                        "artist_name": "Caravaggio",
                        "place_name": (
                            "Museo nazionale di Capodimonte"
                        ),
                        "city": "Napoli",
                        "year": 1607,
                    },
                    {
                        "title": (
                            "Sette opere di Misericordia"
                        ),
                        "artist_name": "Caravaggio",
                        "place_name": (
                            "Pio Monte della Misericordia"
                        ),
                        "city": "Napoli",
                        "year": 1607,
                    },
                    {
                        "title": (
                            "Martirio di sant'Orsola"
                        ),
                        "artist_name": "Caravaggio",
                        "place_name": "Palazzo Zevallos",
                        "city": "Napoli",
                        "year": 1610,
                    },
                ],
            },
        )

        answer = self.renderer.render([execution])

        self.assertIn(
            "Flagellazione di Cristo",
            answer,
        )
        self.assertIn(
            "Museo nazionale di Capodimonte",
            answer,
        )
        self.assertIn(
            "Sette opere di Misericordia",
            answer,
        )
        self.assertIn(
            "Pio Monte della Misericordia",
            answer,
        )
        self.assertIn(
            "Martirio di sant'Orsola",
            answer,
        )
        self.assertIn(
            "Palazzo Zevallos",
            answer,
        )

    def test_does_not_assign_all_artworks_to_one_place(
        self,
    ) -> None:
        execution = ToolExecution(
            tool_call=LLMToolCall(
                name="list_artworks_by_artist",
                arguments={
                    "artist_name": "Caravaggio",
                    "city": "Napoli",
                },
            ),
            result={
                "count": 2,
                "data": [
                    {
                        "title": "Opera A",
                        "place_name": "Luogo A",
                    },
                    {
                        "title": "Opera B",
                        "place_name": "Luogo B",
                    },
                ],
            },
        )

        answer = self.renderer.render([execution])

        self.assertIn("Opera A si trova presso Luogo A", answer)
        self.assertIn("Opera B si trova presso Luogo B", answer)
        self.assertNotIn(
            "Opera A e Opera B si trovano presso Luogo A",
            answer,
        )

    def test_renders_place_list(
        self,
    ) -> None:
        execution = ToolExecution(
            tool_call=LLMToolCall(
                name="list_places",
                arguments={},
            ),
            result={
                "count": 2,
                "data": [
                    {
                        "uri": "place:1",
                        "name": (
                            "Museo nazionale di Capodimonte"
                        ),
                        "normalized_name": (
                            "museo nazionale di capodimonte"
                        ),
                        "city": "Napoli",
                    },
                    {
                        "uri": "place:2",
                        "name": "Palazzo Zevallos",
                        "normalized_name": "palazzo zevallos",
                        "city": "Napoli",
                    },
                ],
            },
        )

        answer = self.renderer.render([execution])

        self.assertIn(
            "Museo nazionale di Capodimonte",
            answer,
        )
        self.assertIn(
            "Palazzo Zevallos",
            answer,
        )

    def test_renders_safe_not_found_answer(
        self,
    ) -> None:
        execution = ToolExecution(
            tool_call=LLMToolCall(
                name="list_artworks_by_artist",
                arguments={
                    "artist_name": "Artista inesistente",
                    "city": "Napoli",
                },
            ),
            result={
                "count": 0,
                "data": [],
            },
        )

        answer = self.renderer.render([execution])

        self.assertEqual(
            answer,
            (
                "Non ho trovato nel database opere di "
                "Artista inesistente visitabili a Napoli."
            ),
        )

    def test_renders_single_artwork_information(
        self,
    ) -> None:
        execution = ToolExecution(
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
                    "title": "Martirio di sant'Orsola",
                    "artist_name": "Caravaggio",
                    "place_name": "Palazzo Zevallos",
                    "city": "Napoli",
                    "year": 1610,
                    "medium": "Pittura a olio",
                    "description": (
                        "Dipinto di Caravaggio."
                    ),
                },
            },
        )

        answer = self.renderer.render([execution])

        self.assertIn(
            "Martirio di sant'Orsola",
            answer,
        )
        self.assertIn("Caravaggio", answer)
        self.assertIn("Palazzo Zevallos", answer)
        self.assertIn("1610", answer)
        self.assertIn(
            "\u00e8 attribuita a Caravaggio",
            answer,
        )
        self.assertIn(
            "\u00e8 datata 1610",
            answer,
        )
        self.assertIn(
            "la tecnica indicata \u00e8 Pittura a olio",
            answer,
        )
        self.assertNotIn("?", answer)

    def test_renders_only_requested_artwork_date(
        self,
    ) -> None:
        execution = ToolExecution(
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
                    "title": "Martirio di sant'Orsola",
                    "artist_name": "Caravaggio",
                    "place_name": "Palazzo Zevallos",
                    "city": "Napoli",
                    "year": 1610,
                    "medium": "Pittura a olio",
                    "description": (
                        "Dipinto di Caravaggio."
                    ),
                },
            },
        )

        answer = self.renderer.render([execution])

        self.assertEqual(
            answer,
            (
                "Martirio di sant'Orsola "
                "\u00e8 stato realizzato nel 1610."
            ),
        )
        self.assertNotIn("Caravaggio", answer)
        self.assertNotIn("Palazzo Zevallos", answer)
        self.assertNotIn("Pittura a olio", answer)

    def test_renders_only_requested_artwork_fields(
        self,
    ) -> None:
        artwork_data = {
            "title": "Martirio di sant'Orsola",
            "artist_name": "Caravaggio",
            "place_name": "Palazzo Zevallos",
            "city": "Napoli",
            "year": 1610,
            "medium": "Pittura a olio",
            "description": "Dipinto di Caravaggio.",
        }

        cases = [
            (
                "author",
                (
                    "Martirio di sant'Orsola "
                    "\u00e8 attribuita a Caravaggio."
                ),
            ),
            (
                "location",
                (
                    "Martirio di sant'Orsola si trova "
                    "presso Palazzo Zevallos, a Napoli."
                ),
            ),
            (
                "description",
                (
                    "Martirio di sant'Orsola: "
                    "Dipinto di Caravaggio."
                ),
            ),
        ]

        for requested_information, expected in cases:
            with self.subTest(
                requested_information=requested_information
            ):
                execution = ToolExecution(
                    tool_call=LLMToolCall(
                        name="get_artwork_information",
                        arguments={
                            "artwork_title": (
                                "Martirio di sant'Orsola"
                            ),
                            "requested_information": (
                                requested_information
                            ),
                        },
                    ),
                    result={
                        "found": True,
                        "data": artwork_data,
                    },
                )

                answer = self.renderer.render(
                    [execution]
                )

                self.assertEqual(answer, expected)

    def test_combines_multiple_tool_results(
        self,
    ) -> None:
        executions = [
            ToolExecution(
                tool_call=LLMToolCall(
                    name="get_artwork_information",
                    arguments={
                        "artwork_title": "Flagellazione"
                    },
                ),
                result={
                    "found": True,
                    "data": {
                        "title": "Flagellazione di Cristo",
                        "year": 1607,
                    },
                },
            ),
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
                        "name": "Caravaggio",
                        "full_name": (
                            "Michelangelo Merisi"
                        ),
                    },
                },
            ),
        ]

        answer = self.renderer.render(executions)

        self.assertIn(
            "Flagellazione di Cristo",
            answer,
        )
        self.assertIn("1607", answer)
        self.assertIn(
            "Michelangelo Merisi",
            answer,
        )


if __name__ == "__main__":
    unittest.main()
