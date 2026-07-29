from dataclasses import replace

from src.core.enums import EntityType, Intent
from src.core.interfaces import (
    KnowledgeRepository,
    MemoryRepository,
)
from src.core.models import (
    DialogueState,
    EntityMention,
    NLUResult,
)


class ContextResolver:
    def __init__(
        self,
        knowledge_repository: KnowledgeRepository,
        memory_repository: MemoryRepository,
    ) -> None:
        self._knowledge_repository = knowledge_repository
        self._memory_repository = memory_repository

    def resolve(
        self,
        session_id: str,
        nlu_result: NLUResult,
    ) -> NLUResult:
        state = self._memory_repository.load_state(
            session_id
        )

        if state is None:
            return nlu_result

        if nlu_result.intent == Intent.FOLLOW_UP:
            return self._resolve_follow_up(
                nlu_result,
                state,
            )

        if self._requires_artwork(
            nlu_result.intent
        ) and not self._has_entity(
            nlu_result,
            EntityType.ARTWORK,
        ):
            artwork_entity = self._artwork_entity(
                state.current_artwork_uri
            )

            if artwork_entity is not None:
                return self._append_entity(
                    nlu_result,
                    artwork_entity,
                )

        return nlu_result

    def _resolve_follow_up(
        self,
        nlu_result: NLUResult,
        state: DialogueState,
    ) -> NLUResult:
        normalized_text = nlu_result.normalized_text

        if (
            "altre" in normalized_text
            or "altri" in normalized_text
        ):
            artist_entity = self._artist_entity(
                state.current_artist_uri
            )

            if artist_entity is not None:
                return replace(
                    nlu_result,
                    intent=(
                        Intent
                        .LIST_ARTWORKS_BY_ARTIST
                    ),
                    intent_confidence=0.90,
                    entities=[
                        *nlu_result.entities,
                        artist_entity,
                    ],
                )

        artwork_entity = self._artwork_entity(
            state.current_artwork_uri
        )

        if artwork_entity is not None:
            return replace(
                nlu_result,
                intent=Intent.ARTWORK_DESCRIPTION,
                intent_confidence=0.90,
                entities=[
                    *nlu_result.entities,
                    artwork_entity,
                ],
            )

        artist_entity = self._artist_entity(
            state.current_artist_uri
        )

        if artist_entity is not None:
            return replace(
                nlu_result,
                intent=Intent.ARTIST_INFO,
                intent_confidence=0.90,
                entities=[
                    *nlu_result.entities,
                    artist_entity,
                ],
            )

        return nlu_result

    @staticmethod
    def _requires_artwork(
        intent: Intent,
    ) -> bool:
        return intent in {
            Intent.ARTWORK_LOCATION,
            Intent.ARTWORK_AUTHOR,
            Intent.ARTWORK_DATE,
            Intent.ARTWORK_DESCRIPTION,
        }

    @staticmethod
    def _has_entity(
        nlu_result: NLUResult,
        entity_type: EntityType,
    ) -> bool:
        return any(
            entity.entity_type == entity_type
            for entity in nlu_result.entities
        )

    @staticmethod
    def _append_entity(
        nlu_result: NLUResult,
        entity: EntityMention,
    ) -> NLUResult:
        return replace(
            nlu_result,
            entities=[
                *nlu_result.entities,
                entity,
            ],
        )

    def _artwork_entity(
        self,
        artwork_uri: str | None,
    ) -> EntityMention | None:
        if artwork_uri is None:
            return None

        artwork = (
            self._knowledge_repository
            .get_artwork_by_uri(artwork_uri)
        )

        if artwork is None:
            return None

        return EntityMention(
            entity_type=EntityType.ARTWORK,
            text=artwork.title,
            canonical_name=artwork.title,
            uri=artwork.uri,
            confidence=1.0,
        )

    def _artist_entity(
        self,
        artist_uri: str | None,
    ) -> EntityMention | None:
        if artist_uri is None:
            return None

        artist = (
            self._knowledge_repository
            .get_artist_by_uri(artist_uri)
        )

        if artist is None:
            return None

        return EntityMention(
            entity_type=EntityType.ARTIST,
            text=artist.name,
            canonical_name=artist.name,
            uri=artist.uri,
            confidence=1.0,
        )
