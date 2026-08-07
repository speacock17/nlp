import unittest
from unittest.mock import MagicMock

from src.core.enums import (
    InconsistencyType,
    Intent,
)
from src.core.models import (
    BotResponse,
    DialogueState,
)
from src.database.mock_knowledge_repository import (
    MockKnowledgeRepository,
)
from src.database.mock_memory_repository import (
    MockMemoryRepository,
)
from src.dialogue.hybrid_chatbot_service import (
    HybridChatbotService,
)
from src.llm.ollama_llm_client import LLMToolCall
from src.llm.tool_calling_agent import (
    AgentResult,
    ToolExecution,
)


def artwork_data() -> dict:
    return {
        "uri": "http://dbpedia.org/resource/The_Martyrdom_of_Saint_Ursula_(Caravaggio)",
        "title": "Martirio di sant'Orsola",
        "normalized_title": "martirio di sant orsola",
        "artist_uri": "artist:caravaggio",
        "artist_name": "Caravaggio",
        "place_uri": "place:zevallos",
        "place_name": "Palazzo Zevallos",
        "city": "Napoli",
        "year": 1610,
        "completion_date": None,
        "medium": None,
        "subject": None,
        "description": (
            "Ultima opera attribuita a Caravaggio."
        ),
        "image_url": None,
        "source": "DBpedia",
    }


class HybridChatbotServiceTest(unittest.TestCase):
    def setUp(self) -> None:
        self.knowledge_repository = (
            MockKnowledgeRepository()
        )
        self.memory_repository = MockMemoryRepository()
        self.agent = MagicMock()
        self.fallback_service = MagicMock()

        self.service = HybridChatbotService(
            knowledge_repository=(
                self.knowledge_repository
            ),
            memory_repository=self.memory_repository,
            agent=self.agent,
            fallback_service=self.fallback_service,
        )

    def test_uses_agent_for_flexible_question(
        self,
    ) -> None:
        self.agent.run.return_value = AgentResult(
            content=(
                "A Napoli puoi vedere diverse opere "
                "di Caravaggio."
            ),
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
                        "data": [artwork_data()],
                    },
                )
            ],
        )

        response = self.service.process(
            session_id="session-1",
            text=(
                "Mi piacerebbe fare un giro per vedere "
                "qualche quadro del Merisi in citt?."
            ),
        )

        self.assertEqual(
            response.intent,
            Intent.LIST_ARTWORKS_BY_ARTIST,
        )
        self.assertEqual(len(response.artworks), 1)

        state = self.memory_repository.load_state(
            "session-1"
        )
        turns = (
            self.memory_repository.get_recent_turns(
                "session-1"
            )
        )

        self.assertEqual(state.turn_index, 1)
        self.assertEqual(len(turns), 1)
        self.assertEqual(
            turns[0].intent,
            Intent.LIST_ARTWORKS_BY_ARTIST,
        )
        self.fallback_service.process.assert_not_called()

    def test_list_places_bypasses_agent(
        self,
    ) -> None:
        response = self.service.process(
            session_id="session-1",
            text="Quali musei posso visitare a Napoli?",
        )

        self.assertEqual(
            response.intent,
            Intent.LIST_PLACES,
        )
        self.assertEqual(len(response.places), 7)
        self.assertIn(
            "Museo nazionale di Capodimonte",
            response.text,
        )
        self.assertIn(
            "Palazzo Zevallos",
            response.text,
        )
        self.agent.run.assert_not_called()
        self.fallback_service.process.assert_not_called()

        state = self.memory_repository.load_state(
            "session-1"
        )
        self.assertEqual(state.turn_index, 1)
        self.assertEqual(
            state.last_intent,
            Intent.LIST_PLACES,
        )

    def test_preserves_deterministic_inconsistency(
        self,
    ) -> None:
        response = self.service.process(
            session_id="session-1",
            text=(
                "Il Martirio di sant'Orsola è di "
                "Battistello Caracciolo?"
            ),
        )

        self.assertIsNotNone(
            response.inconsistency
        )
        self.assertEqual(
            response.inconsistency
            .inconsistency_type,
            InconsistencyType.WRONG_AUTHOR,
        )
        self.assertIn(
            "Caravaggio",
            response.text,
        )
        self.agent.run.assert_not_called()

        state = self.memory_repository.load_state(
            "session-1"
        )
        self.assertEqual(state.turn_index, 1)

    def test_detects_wrong_author_inside_date_question(
        self,
    ) -> None:
        response = self.service.process(
            session_id="session-1",
            text=(
                "Quando \u00e8 stato realizzato il "
                "Martirio di sant'Orsola di "
                "Battistello Caracciolo?"
            ),
        )

        self.assertIsNotNone(
            response.inconsistency
        )
        self.assertEqual(
            response.inconsistency
            .inconsistency_type,
            InconsistencyType.WRONG_AUTHOR,
        )
        self.assertIn(
            "Caravaggio",
            response.text,
        )
        self.agent.run.assert_not_called()

        state = self.memory_repository.load_state(
            "session-1"
        )
        self.assertEqual(state.turn_index, 1)

    def test_passes_resolved_context_to_agent(
        self,
    ) -> None:
        self.agent.run.side_effect = [
            AgentResult(
                content=(
                    "Il Martirio di sant'Orsola è "
                    "un'opera di Caravaggio."
                ),
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
                            "data": artwork_data(),
                        },
                    )
                ],
            ),
            AgentResult(
                content=(
                    "L'opera si trova a Palazzo Zevallos."
                ),
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
                            "data": artwork_data(),
                        },
                    )
                ],
            ),
        ]

        self.service.process(
            session_id="session-1",
            text=(
                "Descrivimi il Martirio "
                "di sant'Orsola"
            ),
        )

        response = self.service.process(
            session_id="session-1",
            text="Dove si trova?",
        )

        second_prompt = (
            self.agent.run.call_args_list[1].args[0]
        )

        self.assertIn(
            "Martirio di sant'Orsola",
            second_prompt,
        )
        self.assertEqual(
            response.intent,
            Intent.ARTWORK_LOCATION,
        )
        self.assertEqual(
            response.artworks[0].place_name,
            "Palazzo Zevallos",
        )

        state = self.memory_repository.load_state(
            "session-1"
        )
        self.assertEqual(state.turn_index, 2)

    def test_ordinal_reference_uses_last_result_order(
        self,
    ) -> None:
        first_artwork = (
            self.knowledge_repository
            .get_artwork_by_title(
                "Flagellazione di Cristo (Caravaggio)"
            )
        )
        second_artwork = (
            self.knowledge_repository
            .get_artwork_by_title(
                "Sette opere di Misericordia"
            )
        )
        third_artwork = (
            self.knowledge_repository
            .get_artwork_by_title(
                "Martirio di sant'Orsola"
            )
        )

        self.memory_repository.save_state(
            DialogueState(
                session_id="session-1",
                current_artwork_uri=first_artwork.uri,
                last_result_uris=[
                    first_artwork.uri,
                    second_artwork.uri,
                    third_artwork.uri,
                ],
            )
        )

        second_artwork_data = {
            **artwork_data(),
            "uri": second_artwork.uri,
            "title": second_artwork.title,
            "normalized_title": (
                second_artwork.normalized_title
            ),
            "place_uri": second_artwork.place_uri,
            "place_name": second_artwork.place_name,
            "year": second_artwork.year,
            "description": second_artwork.description,
        }

        self.agent.run.return_value = AgentResult(
            content=(
                "Sette opere di Misericordia si trova "
                "presso Pio Monte della Misericordia, "
                "a Napoli."
            ),
            executions=[
                ToolExecution(
                    tool_call=LLMToolCall(
                        name="get_artwork_information",
                        arguments={
                            "artwork_title": (
                                "Sette opere di Misericordia"
                            ),
                            "requested_information": (
                                "location"
                            ),
                        },
                    ),
                    result={
                        "found": True,
                        "data": second_artwork_data,
                    },
                )
            ],
        )

        response = self.service.process(
            session_id="session-1",
            text=(
                "Dove si trova il secondo elencato?"
            ),
        )

        prompt = self.agent.run.call_args.args[0]

        self.assertIn(
            "Sette opere di Misericordia",
            prompt,
        )
        self.assertNotIn(
            "Flagellazione di Cristo (Caravaggio)",
            prompt,
        )
        self.assertEqual(
            response.intent,
            Intent.ARTWORK_LOCATION,
        )
        self.assertEqual(
            response.artworks[0].uri,
            second_artwork.uri,
        )
        self.assertEqual(
            response.artworks[0].place_name,
            "Pio Monte della Misericordia",
        )
        self.fallback_service.process.assert_not_called()

    def test_ordinal_list_survives_single_result_follow_ups(
        self,
    ) -> None:
        first_artwork = (
            self.knowledge_repository
            .get_artwork_by_title(
                "Flagellazione di Cristo (Caravaggio)"
            )
        )
        second_artwork = (
            self.knowledge_repository
            .get_artwork_by_title(
                "Sette opere di Misericordia"
            )
        )
        third_artwork = (
            self.knowledge_repository
            .get_artwork_by_title(
                "Martirio di sant'Orsola"
            )
        )

        def data_for(artwork) -> dict:
            return {
                **artwork_data(),
                "uri": artwork.uri,
                "title": artwork.title,
                "normalized_title": (
                    artwork.normalized_title
                ),
                "place_uri": artwork.place_uri,
                "place_name": artwork.place_name,
                "year": artwork.year,
                "description": artwork.description,
            }

        ordered_artworks = [
            first_artwork,
            second_artwork,
            third_artwork,
        ]
        ordered_uris = [
            artwork.uri
            for artwork in ordered_artworks
        ]

        self.agent.run.side_effect = [
            AgentResult(
                content=(
                    "Nel database risultano 3 opere "
                    "di Caravaggio visitabili a Napoli."
                ),
                executions=[
                    ToolExecution(
                        tool_call=LLMToolCall(
                            name=(
                                "list_artworks_by_artist"
                            ),
                            arguments={
                                "artist_name": "Caravaggio",
                                "city": "Napoli",
                            },
                        ),
                        result={
                            "count": 3,
                            "data": [
                                data_for(artwork)
                                for artwork
                                in ordered_artworks
                            ],
                        },
                    )
                ],
            ),
            AgentResult(
                content=(
                    "Sette opere di Misericordia "
                    "si trova presso Pio Monte "
                    "della Misericordia, a Napoli."
                ),
                executions=[
                    ToolExecution(
                        tool_call=LLMToolCall(
                            name=(
                                "get_artwork_information"
                            ),
                            arguments={
                                "artwork_title": (
                                    second_artwork.title
                                ),
                                "requested_information": (
                                    "location"
                                ),
                            },
                        ),
                        result={
                            "found": True,
                            "data": data_for(
                                second_artwork
                            ),
                        },
                    )
                ],
            ),
            AgentResult(
                content=(
                    "Sette opere di Misericordia "
                    "? stato realizzato nel 1607."
                ),
                executions=[
                    ToolExecution(
                        tool_call=LLMToolCall(
                            name=(
                                "get_artwork_information"
                            ),
                            arguments={
                                "artwork_title": (
                                    second_artwork.title
                                ),
                                "requested_information": (
                                    "date"
                                ),
                            },
                        ),
                        result={
                            "found": True,
                            "data": data_for(
                                second_artwork
                            ),
                        },
                    )
                ],
            ),
            AgentResult(
                content=(
                    "Martirio di sant'Orsola si trova "
                    "presso Palazzo Zevallos, a Napoli."
                ),
                executions=[
                    ToolExecution(
                        tool_call=LLMToolCall(
                            name=(
                                "get_artwork_information"
                            ),
                            arguments={
                                "artwork_title": (
                                    third_artwork.title
                                ),
                                "requested_information": (
                                    "location"
                                ),
                            },
                        ),
                        result={
                            "found": True,
                            "data": data_for(
                                third_artwork
                            ),
                        },
                    )
                ],
            ),
        ]

        self.service.process(
            session_id="session-1",
            text=(
                "Quali sono le opere di Caravaggio "
                "a Napoli?"
            ),
        )
        self.service.process(
            session_id="session-1",
            text=(
                "Dove si trova il secondo elencato?"
            ),
        )
        self.service.process(
            session_id="session-1",
            text="A quando risale il dipinto?",
        )
        final_response = self.service.process(
            session_id="session-1",
            text=(
                "Mentre il terzo elencato "
                "dove si trova?"
            ),
        )

        final_prompt = (
            self.agent.run.call_args_list[3].args[0]
        )
        final_state = (
            self.memory_repository.load_state(
                "session-1"
            )
        )

        self.assertIn(
            third_artwork.title,
            final_prompt,
        )
        self.assertEqual(
            final_response.intent,
            Intent.ARTWORK_LOCATION,
        )
        self.assertEqual(
            final_response.artworks[0].uri,
            third_artwork.uri,
        )
        self.assertEqual(
            final_response.artworks[0].place_name,
            "Palazzo Zevallos",
        )
        self.assertEqual(
            final_state.last_result_uris,
            ordered_uris,
        )
        self.assertEqual(
            final_state.current_artwork_uri,
            third_artwork.uri,
        )
        self.fallback_service.process.assert_not_called()

    def test_unknown_paraphrase_uses_current_artwork(
        self,
    ) -> None:
        artwork = (
            self.knowledge_repository
            .get_artwork_by_title(
                "Martirio di sant'Orsola"
            )
        )
        self.memory_repository.save_state(
            DialogueState(
                session_id="session-1",
                current_artwork_uri=artwork.uri,
            )
        )

        self.agent.run.return_value = AgentResult(
            content=(
                "Martirio di sant'Orsola "
                "\u00e8 attribuita a Caravaggio."
            ),
            executions=[
                ToolExecution(
                    tool_call=LLMToolCall(
                        name="get_artwork_information",
                        arguments={
                            "artwork_title": (
                                "Martirio di sant'Orsola"
                            ),
                            "requested_information": "author",
                        },
                    ),
                    result={
                        "found": True,
                        "data": artwork_data(),
                    },
                )
            ],
        )

        response = self.service.process(
            session_id="session-1",
            text="Da chi \u00e8 stato dipinto?",
        )

        prompt = self.agent.run.call_args.args[0]

        self.assertIn(
            "Martirio di sant'Orsola",
            prompt,
        )
        self.assertIn(
            "Da chi \u00e8 stato dipinto?",
            prompt,
        )
        self.assertEqual(
            response.intent,
            Intent.ARTWORK_AUTHOR,
        )
        self.assertEqual(
            response.text,
            (
                "Martirio di sant'Orsola "
                "\u00e8 attribuita a Caravaggio."
            ),
        )
        self.fallback_service.process.assert_not_called()

    def test_uses_fallback_when_agent_fails(
        self,
    ) -> None:
        self.agent.run.side_effect = RuntimeError(
            "Ollama non disponibile"
        )
        fallback_response = BotResponse(
            text="Risposta deterministica.",
            intent=Intent.UNKNOWN,
        )
        self.fallback_service.process.return_value = (
            fallback_response
        )

        response = self.service.process(
            session_id="session-1",
            text="Domanda di prova",
        )

        self.assertIs(
            response,
            fallback_response,
        )
        self.fallback_service.process.assert_called_once_with(
            session_id="session-1",
            text="Domanda di prova",
        )

    def test_context_does_not_force_out_of_scope_question(
        self,
    ) -> None:
        artwork = (
            self.knowledge_repository
            .get_artwork_by_title(
                "Martirio di sant'Orsola"
            )
        )
        self.memory_repository.save_state(
            DialogueState(
                session_id="session-1",
                current_artwork_uri=artwork.uri,
            )
        )

        self.agent.run.return_value = AgentResult(
            content=(
                "Posso rispondere soltanto sulle opere "
                "di Caravaggio e Battistello a Napoli."
            ),
            executions=[],
        )

        response = self.service.process(
            session_id="session-1",
            text="Raccontami una barzelletta",
        )

        prompt = self.agent.run.call_args.args[0]

        self.assertIn(
            "Martirio di sant'Orsola",
            prompt,
        )
        self.assertIn(
            (
                "Usa il contesto soltanto se la domanda "
                "dell'utente vi fa riferimento."
            ),
            prompt,
        )
        self.assertIn(
            (
                "Ignoralo se la nuova domanda non "
                "\u00e8 pertinente."
            ),
            prompt,
        )
        self.assertEqual(
            response.intent,
            Intent.UNKNOWN,
        )
        self.assertEqual(
            response.text,
            (
                "Posso rispondere soltanto sulle opere "
                "di Caravaggio e Battistello a Napoli."
            ),
        )
        self.assertEqual(response.artworks, [])
        self.fallback_service.process.assert_not_called()

    def test_maps_direct_out_of_scope_response(
        self,
    ) -> None:
        self.agent.run.return_value = AgentResult(
            content=(
                "Posso rispondere soltanto sulle opere "
                "di Caravaggio e Battistello a Napoli."
            ),
            executions=[],
        )

        response = self.service.process(
            session_id="session-1",
            text="Che tempo fa oggi?",
        )

        self.assertEqual(
            response.intent,
            Intent.OUT_OF_SCOPE,
        )
        self.assertEqual(response.artworks, [])
        self.assertEqual(response.artists, [])
        self.assertEqual(response.places, [])


if __name__ == "__main__":
    unittest.main()
