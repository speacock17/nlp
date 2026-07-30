import unittest
from unittest.mock import MagicMock

from src.core.enums import (
    InconsistencyType,
    Intent,
)
from src.core.models import BotResponse
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
