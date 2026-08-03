import unittest
from datetime import datetime, timezone

from src.core.enums import (
    EntityType,
    InconsistencyType,
    Intent,
)
from src.core.interfaces import MemoryRepository
from src.core.models import (
    ConversationTurn,
    DialogueState,
    EntityMention,
    Inconsistency,
)
from src.database.mock_memory_repository import (
    MockMemoryRepository,
)


class MockMemoryRepositoryTest(unittest.TestCase):
    def setUp(self) -> None:
        self.repository = MockMemoryRepository()
        self.session_id = "test-session"

    def test_implements_shared_interface(self) -> None:
        self.assertIsInstance(
            self.repository,
            MemoryRepository,
        )

    def test_create_and_load_session(self) -> None:
        created = self.repository.create_session(
            self.session_id
        )
        loaded = self.repository.load_state(
            self.session_id
        )

        self.assertIsInstance(created, DialogueState)
        self.assertEqual(created, loaded)
        self.assertEqual(created.session_id, self.session_id)
        self.assertEqual(created.turn_index, 0)

    def test_create_session_is_idempotent(self) -> None:
        state = DialogueState(
            session_id=self.session_id,
            turn_index=3,
            last_intent=Intent.ARTIST_INFO,
            updated_at=datetime.now(timezone.utc),
        )

        self.repository.save_state(state)

        recreated = self.repository.create_session(
            self.session_id
        )

        self.assertEqual(recreated, state)

    def test_save_and_load_complete_state(self) -> None:
        state = DialogueState(
            session_id=self.session_id,
            turn_index=2,
            last_intent=Intent.ARTWORK_LOCATION,
            current_artist_uri=(
                "http://dbpedia.org/resource/Caravaggio"
            ),
            current_artwork_uri="urn:artwork:test",
            current_place_uri="urn:place:test",
            last_result_uris=[
                "urn:artwork:test",
                "urn:artwork:test-2",
            ],
            pending_clarification="Scegliere un'opera",
            clarification_options=[
                "Opera uno",
                "Opera due",
            ],
            updated_at=datetime.now(timezone.utc),
        )

        self.repository.save_state(state)

        loaded = self.repository.load_state(
            self.session_id
        )

        self.assertEqual(loaded, state)

    def test_saved_state_is_independent_copy(self) -> None:
        state = DialogueState(
            session_id=self.session_id,
            last_result_uris=["urn:artwork:one"],
        )

        self.repository.save_state(state)
        state.last_result_uris.append("urn:artwork:two")

        loaded = self.repository.load_state(
            self.session_id
        )

        self.assertEqual(
            loaded.last_result_uris,
            ["urn:artwork:one"],
        )

    def test_save_state_removes_obsolete_values(self) -> None:
        initial = DialogueState(
            session_id=self.session_id,
            current_artist_uri="urn:artist:test",
            pending_clarification="Confermare",
            updated_at=datetime.now(timezone.utc),
        )
        cleared = DialogueState(
            session_id=self.session_id,
            updated_at=datetime.now(timezone.utc),
        )

        self.repository.save_state(initial)
        self.repository.save_state(cleared)

        loaded = self.repository.load_state(
            self.session_id
        )

        self.assertEqual(loaded, cleared)
        self.assertIsNone(loaded.current_artist_uri)
        self.assertIsNone(loaded.pending_clarification)

    def test_save_and_load_turn_with_entities(self) -> None:
        turn = ConversationTurn(
            session_id=self.session_id,
            turn_index=1,
            user_text="Chi ha dipinto quest'opera?",
            assistant_text="L'ha dipinta Caravaggio.",
            intent=Intent.ARTWORK_AUTHOR,
            timestamp=datetime.now(timezone.utc),
            entities=[
                EntityMention(
                    entity_type=EntityType.ARTWORK,
                    text="quest'opera",
                    canonical_name="Opera di prova",
                    uri="urn:artwork:test",
                    confidence=0.95,
                    start=15,
                    end=26,
                )
            ],
        )

        self.repository.save_turn(turn)

        turns = self.repository.get_recent_turns(
            self.session_id
        )

        self.assertEqual(turns, [turn])
        self.assertEqual(turns[0].entities, turn.entities)

    def test_save_and_load_turn_with_inconsistency(
        self,
    ) -> None:
        turn = ConversationTurn(
            session_id=self.session_id,
            turn_index=1,
            user_text="È conservata a Capodimonte?",
            assistant_text="No, si trova a Palazzo Zevallos.",
            intent=Intent.ARTWORK_LOCATION,
            timestamp=datetime.now(timezone.utc),
            inconsistency=Inconsistency(
                inconsistency_type=(
                    InconsistencyType.WRONG_LOCATION
                ),
                message="Il luogo indicato non è corretto.",
                claimed_value="Capodimonte",
                correct_value="Palazzo Zevallos",
            ),
        )

        self.repository.save_turn(turn)

        turns = self.repository.get_recent_turns(
            self.session_id
        )

        self.assertEqual(turns, [turn])
        self.assertEqual(
            turns[0].inconsistency,
            turn.inconsistency,
        )

    def test_save_turn_is_idempotent(self) -> None:
        turn = ConversationTurn(
            session_id=self.session_id,
            turn_index=1,
            user_text="Domanda",
            assistant_text="Risposta",
            intent=Intent.UNKNOWN,
            timestamp=datetime.now(timezone.utc),
        )

        self.repository.save_turn(turn)
        self.repository.save_turn(turn)

        turns = self.repository.get_recent_turns(
            self.session_id
        )

        self.assertEqual(turns, [turn])

    def test_recent_turns_are_returned_chronologically(
        self,
    ) -> None:
        turns = [
            ConversationTurn(
                session_id=self.session_id,
                turn_index=index,
                user_text=f"Domanda {index}",
                assistant_text=f"Risposta {index}",
                intent=Intent.FOLLOW_UP,
                timestamp=datetime.now(timezone.utc),
            )
            for index in range(1, 4)
        ]

        for turn in turns:
            self.repository.save_turn(turn)

        recent = self.repository.get_recent_turns(
            self.session_id,
            limit=2,
        )

        self.assertEqual(recent, turns[-2:])
        self.assertEqual(
            [turn.turn_index for turn in recent],
            [2, 3],
        )

    def test_save_turn_creates_missing_session(self) -> None:
        self.assertIsNone(
            self.repository.load_state(self.session_id)
        )

        turn = ConversationTurn(
            session_id=self.session_id,
            turn_index=1,
            user_text="Domanda",
            assistant_text="Risposta",
            intent=Intent.UNKNOWN,
            timestamp=datetime.now(timezone.utc),
        )

        self.repository.save_turn(turn)

        self.assertIsNotNone(
            self.repository.load_state(self.session_id)
        )
        self.assertEqual(
            self.repository.get_recent_turns(
                self.session_id
            ),
            [turn],
        )

    def test_clear_session_removes_state_and_turns(
        self,
    ) -> None:
        self.repository.create_session(self.session_id)

        self.repository.save_turn(
            ConversationTurn(
                session_id=self.session_id,
                turn_index=1,
                user_text="Domanda",
                assistant_text="Risposta",
                intent=Intent.UNKNOWN,
                timestamp=datetime.now(timezone.utc),
            )
        )

        self.repository.clear_session(self.session_id)

        self.assertIsNone(
            self.repository.load_state(self.session_id)
        )
        self.assertEqual(
            self.repository.get_recent_turns(
                self.session_id
            ),
            [],
        )

    def test_invalid_recent_turns_limit(self) -> None:
        with self.assertRaises(ValueError):
            self.repository.get_recent_turns(
                self.session_id,
                limit=0,
            )


if __name__ == "__main__":
    unittest.main()
