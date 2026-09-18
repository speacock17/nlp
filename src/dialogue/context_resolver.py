import re
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
    _ARTWORK_INTENTS = {
        Intent.ARTWORK_LOCATION,
        Intent.ARTWORK_AUTHOR,
        Intent.ARTWORK_DATE,
        Intent.ARTWORK_DESCRIPTION,
    }

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

        # Un'opera esplicitamente nominata dall'utente
        # ha sempre precedenza sul contesto conversazionale.
        if self._has_entity(
            nlu_result,
            EntityType.ARTWORK,
        ):
            return nlu_result

        normalized_text = nlu_result.normalized_text

        # "le sue opere", "i suoi dipinti", "le altre"...
        artist_list_result = (
            self._resolve_artist_list_reference(
                nlu_result,
                state,
            )
        )

        if artist_list_result is not None:
            return artist_list_result

        # "lui", "lei" riferiti all'artista corrente.
        artist_pronoun_result = (
            self._resolve_artist_pronoun(
                nlu_result,
                state,
            )
        )

        if artist_pronoun_result is not None:
            return artist_pronoun_result

        # "quello di prima", "il quadro precedente"...
        # ? un riferimento temporale, non l'ordinale 1.
        if self._is_previous_reference(
            normalized_text
        ):
            artwork_entity = (
                self._previous_artwork_entity(
                    session_id,
                    state,
                )
            )

            if artwork_entity is not None:
                return self._append_artwork_entity(
                    nlu_result,
                    artwork_entity,
                )

            return nlu_result

        # "l'altra", "l'altro": ? risolvibile solo
        # quando l'insieme attivo contiene esattamente
        # due opere e una delle due ? quella corrente.
        if self._is_other_reference(
            normalized_text
        ):
            artwork_entity = (
                self._other_artwork_entity(state)
            )

            if artwork_entity is not None:
                return self._append_artwork_entity(
                    nlu_result,
                    artwork_entity,
                )

            # Non indoviniamo se esistono pi? candidati.
            return nlu_result

        # "entrambe", "entrambi", "quale delle due"...
        pair_result = self._resolve_pair_reference(
            nlu_result,
            state,
        )

        if pair_result is not None:
            return pair_result

        # Gli ordinali veri continuano ad usare
        # l'ultimo insieme di risultati.
        if self._has_entity(
            nlu_result,
            EntityType.ORDINAL,
        ):
            artwork_entity = (
                self._ordinal_artwork_entity(
                    nlu_result,
                    state,
                )
            )

            if artwork_entity is not None:
                return self._append_artwork_entity(
                    nlu_result,
                    artwork_entity,
                )

            # Manteniamo il comportamento precedente:
            # un ordinale invalido non cade sul current.
            return nlu_result

        if nlu_result.intent == Intent.FOLLOW_UP:
            return self._resolve_follow_up(
                nlu_result,
                state,
            )

        if (
            nlu_result.intent == Intent.UNKNOWN
            and not self._has_entity(
                nlu_result,
                EntityType.ARTWORK,
            )
        ):
            artwork_entity = self._artwork_entity(
                state.current_artwork_uri
            )

            if artwork_entity is not None:
                return self._append_artwork_entity(
                    nlu_result,
                    artwork_entity,
                )

        if (
            self._requires_artwork(
                nlu_result.intent
            )
            and not self._has_entity(
                nlu_result,
                EntityType.ARTWORK,
            )
        ):
            artwork_entity = self._artwork_entity(
                state.current_artwork_uri
            )

            if artwork_entity is not None:
                return self._append_artwork_entity(
                    nlu_result,
                    artwork_entity,
                )

        return nlu_result

    def _resolve_artist_list_reference(
        self,
        nlu_result: NLUResult,
        state: DialogueState,
    ) -> NLUResult | None:
        normalized_text = nlu_result.normalized_text

        possessive_artworks = bool(
            re.search(
                (
                    r"\b(?:sue\s+opere|"
                    r"opere\s+sue|"
                    r"suoi\s+dipinti|"
                    r"dipinti\s+suoi)\b"
                ),
                normalized_text,
            )
        )

        plural_other = bool(
            re.search(
                r"\b(?:altre|altri)\b",
                normalized_text,
            )
        )

        if (
            not possessive_artworks
            and not plural_other
        ):
            return None

        explicit_artist = next(
            (
                entity
                for entity in nlu_result.entities
                if entity.entity_type
                == EntityType.ARTIST
            ),
            None,
        )

        artist_entity = (
            explicit_artist
            or self._artist_entity(
                state.current_artist_uri
            )
        )

        if artist_entity is None:
            return None

        entities = list(nlu_result.entities)

        if explicit_artist is None:
            entities.append(artist_entity)

        return replace(
            nlu_result,
            intent=Intent.LIST_ARTWORKS_BY_ARTIST,
            intent_confidence=0.90,
            entities=entities,
        )

    def _resolve_artist_pronoun(
        self,
        nlu_result: NLUResult,
        state: DialogueState,
    ) -> NLUResult | None:
        if nlu_result.intent not in {
            Intent.UNKNOWN,
            Intent.FOLLOW_UP,
            Intent.ARTIST_INFO,
        }:
            return None

        if not re.search(
            r"\b(?:lui|lei)\b",
            nlu_result.normalized_text,
        ):
            return None

        artist_entity = self._artist_entity(
            state.current_artist_uri
        )

        if artist_entity is None:
            return None

        return replace(
            nlu_result,
            intent=Intent.ARTIST_INFO,
            intent_confidence=0.90,
            entities=[
                *nlu_result.entities,
                artist_entity,
            ],
        )

    def _resolve_follow_up(
        self,
        nlu_result: NLUResult,
        state: DialogueState,
    ) -> NLUResult:
        artwork_entity = self._artwork_entity(
            state.current_artwork_uri
        )

        if artwork_entity is not None:
            return self._append_artwork_entity(
                nlu_result,
                artwork_entity,
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

    def _resolve_pair_reference(
        self,
        nlu_result: NLUResult,
        state: DialogueState,
    ) -> NLUResult | None:
        normalized_text = nlu_result.normalized_text

        if not (
            re.search(
                r"\b(?:entrambe|entrambi)\b",
                normalized_text,
            )
            or "delle due" in normalized_text
            or "dei due" in normalized_text
        ):
            return None

        pair = self._active_artwork_pair(state)

        if pair is None:
            return None

        requested_year = self._extract_year(
            normalized_text
        )

        if requested_year is not None:
            matching = [
                entity
                for entity in pair
                if self._artwork_entity_matches_year(
                    entity,
                    requested_year,
                )
            ]

            if len(matching) == 1:
                return self._append_artwork_entity(
                    nlu_result,
                    matching[0],
                )

        result = nlu_result

        for entity in pair:
            result = self._append_entity(
                result,
                entity,
            )

        inferred_intent = self._infer_artwork_intent(
            result
        )

        if inferred_intent != result.intent:
            result = replace(
                result,
                intent=inferred_intent,
                intent_confidence=0.90,
            )

        return result

    def _previous_artwork_entity(
        self,
        session_id: str,
        state: DialogueState,
    ) -> EntityMention | None:
        turns = self._memory_repository.get_recent_turns(
            session_id,
            limit=10,
        )

        recent_uris: list[str] = []

        for turn in reversed(turns):
            for entity in reversed(turn.entities):
                if (
                    entity.entity_type
                    != EntityType.ARTWORK
                    or entity.uri is None
                    or entity.uri in recent_uris
                ):
                    continue

                recent_uris.append(entity.uri)

        current_uri = state.current_artwork_uri

        if current_uri is not None:
            for artwork_uri in recent_uris:
                if artwork_uri != current_uri:
                    entity = self._artwork_entity(
                        artwork_uri
                    )

                    if entity is not None:
                        return entity

            return self._artwork_entity(current_uri)

        if recent_uris:
            return self._artwork_entity(
                recent_uris[0]
            )

        return None

    def _other_artwork_entity(
        self,
        state: DialogueState,
    ) -> EntityMention | None:
        pair = self._active_artwork_pair(state)

        if (
            pair is None
            or state.current_artwork_uri is None
        ):
            return None

        candidates = [
            entity
            for entity in pair
            if entity.uri
            != state.current_artwork_uri
        ]

        if len(candidates) != 1:
            return None

        if not any(
            entity.uri == state.current_artwork_uri
            for entity in pair
        ):
            return None

        return candidates[0]

    def _active_artwork_pair(
        self,
        state: DialogueState,
    ) -> list[EntityMention] | None:
        if len(state.last_result_uris) != 2:
            return None

        entities = [
            self._artwork_entity(uri)
            for uri in state.last_result_uris
        ]

        if any(
            entity is None
            for entity in entities
        ):
            return None

        return [
            entity
            for entity in entities
            if entity is not None
        ]

    def _ordinal_artwork_entity(
        self,
        nlu_result: NLUResult,
        state: DialogueState,
    ) -> EntityMention | None:
        ordinal_entity = next(
            (
                entity
                for entity in nlu_result.entities
                if entity.entity_type
                == EntityType.ORDINAL
            ),
            None,
        )

        if (
            ordinal_entity is None
            or ordinal_entity.canonical_name is None
            or not state.last_result_uris
        ):
            return None

        ordinal_value = (
            ordinal_entity.canonical_name
        )

        if ordinal_value == "last":
            artwork_uri = state.last_result_uris[-1]
        else:
            try:
                position = int(ordinal_value)
            except ValueError:
                return None

            if (
                position < 1
                or position
                > len(state.last_result_uris)
            ):
                return None

            artwork_uri = (
                state.last_result_uris[position - 1]
            )

        return self._artwork_entity(artwork_uri)

    def _append_artwork_entity(
        self,
        nlu_result: NLUResult,
        entity: EntityMention,
    ) -> NLUResult:
        result = self._append_entity(
            nlu_result,
            entity,
        )

        inferred_intent = self._infer_artwork_intent(
            result
        )

        if inferred_intent == result.intent:
            return result

        return replace(
            result,
            intent=inferred_intent,
            intent_confidence=0.90,
        )

    def _infer_artwork_intent(
        self,
        nlu_result: NLUResult,
    ) -> Intent:
        if nlu_result.intent in self._ARTWORK_INTENTS:
            return nlu_result.intent

        normalized_text = nlu_result.normalized_text

        if (
            "dove" in normalized_text
            or "si trova" in normalized_text
            or "collocata" in normalized_text
            or "collocato" in normalized_text
        ):
            return Intent.ARTWORK_LOCATION

        if (
            "autore" in normalized_text
            or "chi ha dipinto" in normalized_text
            or "chi l ha dipinto" in normalized_text
            or "chi l ha dipinta" in normalized_text
        ):
            return Intent.ARTWORK_AUTHOR

        if (
            "anno" in normalized_text
            or "quando" in normalized_text
            or "data" in normalized_text
            or self._extract_year(
                normalized_text
            )
            is not None
        ):
            return Intent.ARTWORK_DATE

        if nlu_result.intent == Intent.FOLLOW_UP:
            return Intent.ARTWORK_DESCRIPTION

        return nlu_result.intent

    def _artwork_entity_matches_year(
        self,
        entity: EntityMention,
        requested_year: int,
    ) -> bool:
        if entity.uri is None:
            return False

        artwork = (
            self._knowledge_repository
            .get_artwork_by_uri(entity.uri)
        )

        if artwork is None or artwork.year is None:
            return False

        year_numbers = [
            int(value)
            for value in re.findall(
                r"\b\d{4}\b",
                str(artwork.year),
            )
        ]

        if not year_numbers:
            return False

        if len(year_numbers) == 1:
            return year_numbers[0] == requested_year

        start_year = min(year_numbers)
        end_year = max(year_numbers)

        return (
            start_year
            <= requested_year
            <= end_year
        )

    @staticmethod
    def _extract_year(
        normalized_text: str,
    ) -> int | None:
        match = re.search(
            r"\b(1[0-9]{3}|20[0-9]{2})\b",
            normalized_text,
        )

        if match is None:
            return None

        return int(match.group(1))

    @staticmethod
    def _is_previous_reference(
        normalized_text: str,
    ) -> bool:
        return (
            "di prima" in normalized_text
            or bool(
                re.search(
                    (
                        r"\b(?:quadro|opera|dipinto|"
                        r"quello|quella)\s+precedente\b"
                    ),
                    normalized_text,
                )
            )
        )

    @staticmethod
    def _is_other_reference(
        normalized_text: str,
    ) -> bool:
        return bool(
            re.search(
                r"\b(?:l\s+|un\s+)?altr[oa]\b",
                normalized_text,
            )
        )

    @staticmethod
    def _requires_artwork(
        intent: Intent,
    ) -> bool:
        return intent in ContextResolver._ARTWORK_INTENTS

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
