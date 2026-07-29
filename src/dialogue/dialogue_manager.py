from datetime import datetime, timezone

from src.core.interfaces import (
    KnowledgeRepository,
    MemoryRepository,
)
from src.core.models import (
    BotResponse,
    ConversationTurn,
    DialogueState,
    NLUResult,
)


class DialogueManager:
    def __init__(
        self,
        knowledge_repository: KnowledgeRepository,
        memory_repository: MemoryRepository,
    ) -> None:
        self._knowledge_repository = knowledge_repository
        self._memory_repository = memory_repository

    def record_turn(
        self,
        session_id: str,
        nlu_result: NLUResult,
        response: BotResponse,
    ) -> DialogueState:
        state = self._memory_repository.load_state(
            session_id
        )

        if state is None:
            state = self._memory_repository.create_session(
                session_id
            )

        timestamp = datetime.now(
            timezone.utc
        ).replace(tzinfo=None)

        state.turn_index += 1
        state.last_intent = nlu_result.intent
        state.updated_at = timestamp

        if response.artists:
            state.current_artist_uri = (
                response.artists[0].uri
            )

        if response.artworks:
            state.current_artwork_uri = (
                response.artworks[0].uri
            )

        if response.places:
            state.current_place_uri = (
                response.places[0].uri
            )

        state.last_result_uris = (
            self._result_uris(response)
        )

        if response.needs_clarification:
            state.pending_clarification = response.text
            state.clarification_options = list(
                response.clarification_options
            )
        else:
            state.pending_clarification = None
            state.clarification_options = []

        turn = ConversationTurn(
            session_id=session_id,
            turn_index=state.turn_index,
            user_text=nlu_result.raw_text,
            assistant_text=response.text,
            intent=nlu_result.intent,
            timestamp=timestamp,
            entities=list(nlu_result.entities),
            inconsistency=response.inconsistency,
        )

        self._memory_repository.save_state(state)
        self._memory_repository.save_turn(turn)

        return state

    @staticmethod
    def _result_uris(
        response: BotResponse,
    ) -> list[str]:
        if response.artworks:
            return [
                artwork.uri
                for artwork in response.artworks
            ]

        if response.artists:
            return [
                artist.uri
                for artist in response.artists
            ]

        if response.places:
            return [
                place.uri
                for place in response.places
            ]

        return []
