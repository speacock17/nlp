import unittest

from src.core.enums import (
    InconsistencyType,
    Intent,
)
from src.database.mock_knowledge_repository import (
    MockKnowledgeRepository,
)
from src.database.mock_memory_repository import (
    MockMemoryRepository,
)
from src.dialogue.chatbot_service import ChatbotService


class ChatbotServiceTest(unittest.TestCase):
    def setUp(self) -> None:
        self.knowledge_repository = (
            MockKnowledgeRepository()
        )
        self.memory_repository = MockMemoryRepository()
        self.service = ChatbotService(
            knowledge_repository=(
                self.knowledge_repository
            ),
            memory_repository=(
                self.memory_repository
            ),
        )

    def test_processes_complete_question(
        self,
    ) -> None:
        response = self.service.process(
            session_id="session-1",
            text=(
                "Dove si trova il Martirio "
                "di sant'Orsola?"
            ),
        )

        self.assertEqual(
            response.intent,
            Intent.ARTWORK_LOCATION,
        )
        self.assertIn(
            "Palazzo Zevallos",
            response.text,
        )
        self.assertEqual(
            len(response.artworks),
            1,
        )

    def test_detects_inconsistency(
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

    def test_uses_context_for_follow_up(
        self,
    ) -> None:
        self.service.process(
            session_id="session-1",
            text=(
                "Dove si trova il Martirio "
                "di sant'Orsola?"
            ),
        )

        response = self.service.process(
            session_id="session-1",
            text="Dimmi di più",
        )

        self.assertEqual(
            response.intent,
            Intent.ARTWORK_DESCRIPTION,
        )
        self.assertEqual(
            len(response.artworks),
            1,
        )
        self.assertEqual(
            response.artworks[0].title,
            "Martirio di sant'Orsola",
        )

    def test_uses_context_for_incomplete_question(
        self,
    ) -> None:
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

        self.assertEqual(
            response.intent,
            Intent.ARTWORK_LOCATION,
        )
        self.assertIn(
            "Palazzo Zevallos",
            response.text,
        )

    def test_records_state_and_turns(
        self,
    ) -> None:
        self.service.process(
            session_id="session-1",
            text="Parlami di Caravaggio",
        )
        self.service.process(
            session_id="session-1",
            text=(
                "Quali opere di Caravaggio "
                "posso vedere a Napoli?"
            ),
        )

        state = self.memory_repository.load_state(
            "session-1"
        )
        turns = (
            self.memory_repository.get_recent_turns(
                "session-1"
            )
        )

        self.assertEqual(state.turn_index, 2)
        self.assertEqual(len(turns), 2)
        self.assertEqual(
            turns[-1].intent,
            Intent.LIST_ARTWORKS_BY_ARTIST,
        )

    def test_sessions_remain_independent(
        self,
    ) -> None:
        self.service.process(
            session_id="session-1",
            text="Parlami di Caravaggio",
        )
        self.service.process(
            session_id="session-2",
            text=(
                "Parlami di Battistello "
                "Caracciolo"
            ),
        )

        first = self.memory_repository.load_state(
            "session-1"
        )
        second = self.memory_repository.load_state(
            "session-2"
        )

        self.assertEqual(first.turn_index, 1)
        self.assertEqual(second.turn_index, 1)
        self.assertNotEqual(
            first.current_artist_uri,
            second.current_artist_uri,
        )


if __name__ == "__main__":
    unittest.main()
