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

    def test_renders_places_with_artworks_grouped_by_place(
        self,
    ) -> None:
        execution = ToolExecution(
            tool_call=LLMToolCall(
                name="list_places_with_artworks",
                arguments={},
            ),
            result={
                "count": 3,
                "data": [
                    {
                        "uri": "artwork:1",
                        "title": "Cristo alla colonna",
                        "normalized_title": (
                            "cristo alla colonna"
                        ),
                        "artist_uri": "artist:1",
                        "artist_name": (
                            "Battistello Caracciolo"
                        ),
                        "place_uri": "place:1",
                        "place_name": (
                            "Museo nazionale di Capodimonte"
                        ),
                        "city": "Napoli",
                    },
                    {
                        "uri": "artwork:2",
                        "title": (
                            "Flagellazione di Cristo "
                            "(Caravaggio)"
                        ),
                        "normalized_title": (
                            "flagellazione di cristo caravaggio"
                        ),
                        "artist_uri": "artist:2",
                        "artist_name": "Caravaggio",
                        "place_uri": "place:1",
                        "place_name": (
                            "Museo nazionale di Capodimonte"
                        ),
                        "city": "Napoli",
                    },
                    {
                        "uri": "artwork:3",
                        "title": "Martirio di sant'Orsola",
                        "normalized_title": (
                            "martirio di sant orsola"
                        ),
                        "artist_uri": "artist:2",
                        "artist_name": "Caravaggio",
                        "place_uri": "place:2",
                        "place_name": "Palazzo Zevallos",
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
            "Cristo alla colonna",
            answer,
        )
        self.assertIn(
            "Flagellazione di Cristo (Caravaggio)",
            answer,
        )
        self.assertIn(
            "Palazzo Zevallos",
            answer,
        )
        self.assertIn(
            "Martirio di sant'Orsola",
            answer,
        )
        self.assertEqual(
            answer.count(
                "Museo nazionale di Capodimonte"
            ),
            1,
        )
        self.assertEqual(
            answer.count("Palazzo Zevallos"),
            1,
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
            "description": "Dipinto di Caravaggio, test forza",
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
                    "presso Palazzo Zevallos."
                ),
            ),
            (
                "description",
                "Dipinto di Caravaggio, test forza",
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


    def test_renders_only_requested_artist_birth_date(
        self,
    ) -> None:
        execution = ToolExecution(
            tool_call=LLMToolCall(
                name="get_artist_information",
                arguments={
                    "artist_name": "Caravaggio",
                    "requested_fields": ["birth_date"],
                },
            ),
            result={
                "found": True,
                "data": {
                    "name": "Caravaggio",
                    "full_name": "Michelangelo Merisi",
                    "birth_date": "29 settembre 1571",
                    "birth_place": "Ducato di Milano",
                    "death_date": "18 luglio 1610",
                    "death_place": "Porto Ercole",
                    "description": "Pittore italiano.",
                },
            },
        )

        answer = self.renderer.render([execution])

        self.assertIn(
            "29 settembre 1571",
            answer,
        )
        self.assertNotIn(
            "Michelangelo Merisi",
            answer,
        )
        self.assertNotIn(
            "Ducato di Milano",
            answer,
        )
        self.assertNotIn(
            "18 luglio 1610",
            answer,
        )
        self.assertNotIn(
            "Porto Ercole",
            answer,
        )
        self.assertNotIn(
            "Pittore italiano",
            answer,
        )

    def test_renders_requested_artist_birth_date_and_place(
        self,
    ) -> None:
        execution = ToolExecution(
            tool_call=LLMToolCall(
                name="get_artist_information",
                arguments={
                    "artist_name": "Caravaggio",
                    "requested_fields": [
                        "birth_date",
                        "birth_place",
                    ],
                },
            ),
            result={
                "found": True,
                "data": {
                    "name": "Caravaggio",
                    "full_name": "Michelangelo Merisi",
                    "birth_date": "29 settembre 1571",
                    "birth_place": "Ducato di Milano",
                    "death_date": "18 luglio 1610",
                    "death_place": "Porto Ercole",
                    "description": "Pittore italiano.",
                },
            },
        )

        answer = self.renderer.render([execution])

        self.assertIn(
            "29 settembre 1571",
            answer,
        )
        self.assertIn(
            "Ducato di Milano",
            answer,
        )
        self.assertNotIn(
            "18 luglio 1610",
            answer,
        )
        self.assertNotIn(
            "Porto Ercole",
            answer,
        )

    def test_renders_only_requested_artwork_multiple_fields(
        self,
    ) -> None:
        execution = ToolExecution(
            tool_call=LLMToolCall(
                name="get_artwork_information",
                arguments={
                    "artwork_title": (
                        "Martirio di sant'Orsola"
                    ),
                    "requested_fields": [
                        "author",
                        "location",
                        "date",
                    ],
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
                    "completion_date": None,
                    "medium": "Pittura a olio",
                    "subject": "Martirio di sant'Orsola",
                    "description": "Dipinto di Caravaggio.",
                },
            },
        )

        answer = self.renderer.render([execution])

        self.assertIn("Caravaggio", answer)
        self.assertIn("Palazzo Zevallos", answer)
        self.assertIn("1610", answer)

        self.assertNotIn(
            "Pittura a olio",
            answer,
        )
        self.assertNotIn(
            "Martirio di sant'Orsola",
            answer.replace(
                "Martirio di sant'Orsola",
                "",
                1,
            ),
        )
        self.assertNotIn(
            "Dipinto di Caravaggio",
            answer,
        )

    def test_renders_only_requested_artwork_medium_and_subject(
        self,
    ) -> None:
        execution = ToolExecution(
            tool_call=LLMToolCall(
                name="get_artwork_information",
                arguments={
                    "artwork_title": "Opera test",
                    "requested_fields": [
                        "medium",
                        "subject",
                    ],
                },
            ),
            result={
                "found": True,
                "data": {
                    "title": "Opera test",
                    "artist_name": "Artista test",
                    "place_name": "Luogo test",
                    "year": 1600,
                    "medium": "Olio su tela",
                    "subject": "Scena religiosa",
                    "description": "Descrizione test.",
                },
            },
        )

        answer = self.renderer.render([execution])

        self.assertIn("Olio su tela", answer)
        self.assertIn("Scena religiosa", answer)
        self.assertNotIn("Artista test", answer)
        self.assertNotIn("Luogo test", answer)
        self.assertNotIn("1600", answer)
        self.assertNotIn("Descrizione test", answer)

    def test_renders_only_requested_place_address(
        self,
    ) -> None:
        execution = ToolExecution(
            tool_call=LLMToolCall(
                name="get_place_information",
                arguments={
                    "place_name": (
                        "Museo nazionale di Capodimonte"
                    ),
                    "requested_fields": ["address"],
                },
            ),
            result={
                "found": True,
                "data": {
                    "name": (
                        "Museo nazionale di Capodimonte"
                    ),
                    "city": "Napoli",
                    "place_type": "Museo",
                    "address": "Via Miano, 2",
                    "latitude": 40.867,
                    "longitude": 14.250,
                    "description": "Museo napoletano.",
                },
            },
        )

        answer = self.renderer.render([execution])

        self.assertIn("Via Miano, 2", answer)
        self.assertNotIn("Museo napoletano", answer)
        self.assertNotIn("40.867", answer)
        self.assertNotIn("14.25", answer)

    def test_renders_requested_place_coordinates(
        self,
    ) -> None:
        execution = ToolExecution(
            tool_call=LLMToolCall(
                name="get_place_information",
                arguments={
                    "place_name": (
                        "Museo nazionale di Capodimonte"
                    ),
                    "requested_fields": ["coordinates"],
                },
            ),
            result={
                "found": True,
                "data": {
                    "name": (
                        "Museo nazionale di Capodimonte"
                    ),
                    "city": "Napoli",
                    "place_type": "Museo",
                    "address": "Via Miano, 2",
                    "latitude": 40.867,
                    "longitude": 14.250,
                    "description": "Museo napoletano.",
                },
            },
        )

        answer = self.renderer.render([execution])

        self.assertIn("40.867", answer)
        self.assertIn("14.25", answer)
        self.assertNotIn("Via Miano, 2", answer)
        self.assertNotIn("Museo napoletano", answer)

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
