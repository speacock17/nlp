from copy import deepcopy

from src.core.interfaces import MemoryRepository
from src.core.models import ConversationTurn, DialogueState


class MockMemoryRepository(MemoryRepository):
    def __init__(self) -> None:
        self._states: dict[str, DialogueState] = {}
        self._turns: dict[
            str,
            dict[int, ConversationTurn],
        ] = {}

    @staticmethod
    def _validate_limit(limit: int) -> None:
        if limit <= 0:
            raise ValueError(
                "Il limite deve essere maggiore di zero"
            )

    def create_session(
        self,
        session_id: str,
    ) -> DialogueState:
        existing = self.load_state(session_id)

        if existing is not None:
            return existing

        state = DialogueState(session_id=session_id)
        self.save_state(state)

        return deepcopy(state)

    def load_state(
        self,
        session_id: str,
    ) -> DialogueState | None:
        state = self._states.get(session_id)

        if state is None:
            return None

        return deepcopy(state)

    def save_state(
        self,
        state: DialogueState,
    ) -> None:
        self._states[state.session_id] = deepcopy(state)

    def save_turn(
        self,
        turn: ConversationTurn,
    ) -> None:
        if turn.session_id not in self._states:
            self.save_state(
                DialogueState(
                    session_id=turn.session_id,
                    updated_at=turn.timestamp,
                )
            )

        session_turns = self._turns.setdefault(
            turn.session_id,
            {},
        )

        session_turns[turn.turn_index] = deepcopy(turn)

    def get_recent_turns(
        self,
        session_id: str,
        limit: int = 10,
    ) -> list[ConversationTurn]:
        self._validate_limit(limit)

        session_turns = self._turns.get(
            session_id,
            {},
        )

        ordered_turns = sorted(
            session_turns.values(),
            key=lambda turn: turn.turn_index,
        )

        return deepcopy(ordered_turns[-limit:])

    def clear_session(
        self,
        session_id: str,
    ) -> None:
        self._states.pop(session_id, None)
        self._turns.pop(session_id, None)
