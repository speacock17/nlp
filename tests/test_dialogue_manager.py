import unittest

from src.core.enums import Intent
from src.core.models import BotResponse, NLUResult
from src.database.mock_knowledge_repository import (
    MockKnowledgeRepository,
)
from src.database.mock_memory_repository import (
    MockMemoryRepository,
)
from src.dialogue.dialogue_manager import DialogueManager
from src.dialogue.response_generator import ResponseGenerator
from src.nlp.nlu_pipeline import NLUPipeline


class DialogueManagerTest(unittest.TestCase):
    def setUp(self) -> None:
        self.knowledge_repository = (
            MockKnowledgeRepository()
        )
        self.memory_repository = MockMemoryRepository()
        self.pipeline = NLUPipeline(
            self.knowledge_repository
        )
        self.generator = ResponseGenerator(
            self.knowledge_repository
        )
        self.manager = DialogueManager(
            knowledge_repository=(
                self.knowledge_repository
            ),
            memory_repository=(
                self.memory_repository
            ),
        )

    def _process(
        self,
        session_id: str,
        text: str,
    ):
        nlu_result = self.pipeline.analyze(text)
        response = self.generator.generate(nlu_result)

        state = self.manager.record_turn(
            session_id=session_id,
            nlu_result=nlu_result,
            response=response,
        )

        return nlu_result, response, state

    def test_creates_session_and_records_first_turn(
        self,
    ) -> None:
        nlu_result, response, state = self._process(
            "session-1",
            "Quali opere di Caravaggio posso vedere "
            "a Napoli?",
        )

        self.assertEqual(state.session_id, "session-1")
        self.assertEqual(state.turn_index, 1)
        self.assertEqual(
            state.last_intent,
            Intent.LIST_ARTWORKS_BY_ARTIST,
        )

        stored_state = (
            self.memory_repository.load_state(
                "session-1"
            )
        )
        self.assertEqual(stored_state, state)

        turns = (
            self.memory_repository.get_recent_turns(
                "session-1"
            )
        )
        self.assertEqual(len(turns), 1)
        self.assertEqual(
            turns[0].user_text,
            nlu_result.raw_text,
        )
        self.assertEqual(
            turns[0].assistant_text,
            response.text,
        )
        self.assertEqual(
            turns[0].intent,
            nlu_result.intent,
        )

    def test_increments_turn_index(self) -> None:
        self._process(
            "session-1",
            "Parlami di Caravaggio",
        )
        _, _, state = self._process(
            "session-1",
            "Quali opere di Caravaggio posso vedere "
            "a Napoli?",
        )

        self.assertEqual(state.turn_index, 2)

        turns = (
            self.memory_repository.get_recent_turns(
                "session-1"
            )
        )
        self.assertEqual(
            [turn.turn_index for turn in turns],
            [1, 2],
        )

    def test_updates_artist_and_result_context(
        self,
    ) -> None:
        _, response, state = self._process(
            "session-1",
            "Quali opere di Caravaggio posso vedere "
            "a Napoli?",
        )

        self.assertEqual(
            state.current_artist_uri,
            response.artists[0].uri,
        )
        self.assertEqual(
            state.last_result_uris,
            [
                artwork.uri
                for artwork in response.artworks
            ],
        )

    def test_updates_artwork_context(self) -> None:
        _, response, state = self._process(
            "session-1",
            "Dove si trova il Martirio di "
            "sant'Orsola?",
        )

        self.assertEqual(
            state.current_artwork_uri,
            response.artworks[0].uri,
        )
        self.assertEqual(
            state.last_result_uris,
            [response.artworks[0].uri],
        )

    def test_stores_pending_clarification(
        self,
    ) -> None:
        nlu_result = NLUResult(
            raw_text="Quale opera?",
            normalized_text="quale opera",
            intent=Intent.UNKNOWN,
            intent_confidence=0.20,
        )
        response = BotResponse(
            text="Quale opera intendi?",
            intent=Intent.UNKNOWN,
            needs_clarification=True,
            clarification_options=[
                "Martirio di sant'Orsola",
                "Sette opere di Misericordia",
            ],
        )

        state = self.manager.record_turn(
            session_id="session-1",
            nlu_result=nlu_result,
            response=response,
        )

        self.assertEqual(
            state.pending_clarification,
            response.text,
        )
        self.assertEqual(
            state.clarification_options,
            response.clarification_options,
        )

    def test_successful_response_clears_clarification(
        self,
    ) -> None:
        clarification_result = NLUResult(
            raw_text="Quale opera?",
            normalized_text="quale opera",
            intent=Intent.UNKNOWN,
            intent_confidence=0.20,
        )
        clarification_response = BotResponse(
            text="Quale opera intendi?",
            intent=Intent.UNKNOWN,
            needs_clarification=True,
            clarification_options=[
                "Martirio di sant'Orsola",
            ],
        )

        self.manager.record_turn(
            session_id="session-1",
            nlu_result=clarification_result,
            response=clarification_response,
        )

        _, _, state = self._process(
            "session-1",
            "Dove si trova il Martirio di "
            "sant'Orsola?",
        )

        self.assertIsNone(
            state.pending_clarification
        )
        self.assertEqual(
            state.clarification_options,
            [],
        )

    def test_sessions_remain_independent(self) -> None:
        self._process(
            "session-1",
            "Parlami di Caravaggio",
        )
        self._process(
            "session-2",
            "Parlami di Battistello Caracciolo",
        )

        first = self.memory_repository.load_state(
            "session-1"
        )
        second = self.memory_repository.load_state(
            "session-2"
        )

        self.assertNotEqual(
            first.current_artist_uri,
            second.current_artist_uri,
        )
        self.assertEqual(first.turn_index, 1)
        self.assertEqual(second.turn_index, 1)


if __name__ == "__main__":
    unittest.main()
