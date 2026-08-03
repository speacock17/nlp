import re
from collections.abc import Iterable
from difflib import SequenceMatcher

from src.core.constants import (
    FUZZY_MATCH_ACCEPTED_THRESHOLD,
)
from src.core.enums import EntityType
from src.core.interfaces import KnowledgeRepository
from src.core.models import (
    Artist,
    Artwork,
    EntityMention,
    Place,
)
from src.core.normalization import normalize_text


class EntityLinker:
    _ARTIST_NAMES = (
        "Caravaggio",
        "Battistello Caracciolo",
    )

    _ARTIST_ALIASES = {
        "caravaggio": (
            "Caravaggio",
        ),
        "battistello caracciolo": (
            "Battistello Caracciolo",
            "Battistello",
            "Caracciolo",
        ),
    }

    _PLACE_ALIASES = {
        "museo nazionale di capodimonte": (
            "Museo nazionale di Capodimonte",
            "Museo di Capodimonte",
            "Capodimonte",
        ),
        "palazzo zevallos": (
            "Palazzo Zevallos",
            "Zevallos",
        ),
        "pio monte della misericordia": (
            "Pio Monte della Misericordia",
            "Pio Monte",
        ),
        "certosa di san martino": (
            "Certosa di San Martino",
            "San Martino",
        ),
        "quadreria dei girolamini": (
            "Quadreria dei Girolamini",
            "Girolamini",
        ),
        "palazzo reale di napoli": (
            "Palazzo Reale di Napoli",
            "Palazzo Reale",
        ),
        "chiesa di santa maria della stella": (
            "Chiesa di Santa Maria della Stella",
            "Santa Maria della Stella",
        ),
    }

    def __init__(
        self,
        knowledge_repository: KnowledgeRepository,
    ) -> None:
        self._knowledge_repository = knowledge_repository
        self._artists = self._load_artists()
        self._artworks = self._load_artworks()
        self._places = self._load_places()

    def _load_artists(self) -> list[Artist]:
        artists: list[Artist] = []

        for artist_name in self._ARTIST_NAMES:
            artist = (
                self._knowledge_repository
                .get_artist_by_name(artist_name)
            )

            if artist is not None:
                artists.append(artist)

        return artists

    def _load_artworks(self) -> list[Artwork]:
        artworks_by_uri: dict[str, Artwork] = {}

        for artist in self._artists:
            artworks = (
                self._knowledge_repository
                .list_artworks_by_artist(artist.name)
            )

            for artwork in artworks:
                artworks_by_uri[artwork.uri] = artwork

        return list(artworks_by_uri.values())

    def _load_places(self) -> list[Place]:
        places_by_uri: dict[str, Place] = {}

        for artwork in self._artworks:
            if artwork.place_name is None:
                continue

            place = (
                self._knowledge_repository
                .get_place_by_name(artwork.place_name)
            )

            if place is not None:
                places_by_uri[place.uri] = place

        return list(places_by_uri.values())

    @staticmethod
    def _artwork_aliases(
        artwork: Artwork,
    ) -> tuple[str, ...]:
        title_without_parentheses = re.sub(
            r"\s*\([^)]*\)\s*$",
            "",
            artwork.title,
        ).strip()

        if title_without_parentheses == artwork.title:
            return (artwork.title,)

        return (
            artwork.title,
            title_without_parentheses,
        )

    @classmethod
    def _artist_aliases(
        cls,
        artist: Artist,
    ) -> tuple[str, ...]:
        return cls._ARTIST_ALIASES.get(
            artist.normalized_name,
            (artist.name,),
        )

    @classmethod
    def _place_aliases(
        cls,
        place: Place,
    ) -> tuple[str, ...]:
        return cls._PLACE_ALIASES.get(
            place.normalized_name,
            (place.name,),
        )

    @staticmethod
    def _token_spans(
        normalized_text: str,
    ) -> list[tuple[str, int, int]]:
        return [
            (
                match.group(),
                match.start(),
                match.end(),
            )
            for match in re.finditer(
                r"\b[a-z0-9]+\b",
                normalized_text,
            )
        ]

    @classmethod
    def _best_alias_match(
        cls,
        normalized_text: str,
        aliases: Iterable[str],
    ) -> tuple[str, float, int, int] | None:
        tokens = cls._token_spans(normalized_text)
        best_match: tuple[
            str,
            float,
            int,
            int,
        ] | None = None

        for alias in aliases:
            normalized_alias = normalize_text(alias)

            if not normalized_alias:
                continue

            exact_start = normalized_text.find(
                normalized_alias
            )

            if exact_start >= 0:
                candidate = (
                    normalized_text[
                        exact_start:
                        exact_start + len(normalized_alias)
                    ],
                    1.0,
                    exact_start,
                    exact_start + len(normalized_alias),
                )
            else:
                candidate = cls._best_window_match(
                    normalized_alias,
                    tokens,
                )

            if candidate is None:
                continue

            if candidate[1] < (
                FUZZY_MATCH_ACCEPTED_THRESHOLD
            ):
                continue

            if best_match is None:
                best_match = candidate
                continue

            current_length = (
                candidate[3] - candidate[2]
            )
            best_length = (
                best_match[3] - best_match[2]
            )

            if (
                candidate[1] > best_match[1]
                or (
                    candidate[1] == best_match[1]
                    and current_length > best_length
                )
            ):
                best_match = candidate

        return best_match

    @staticmethod
    def _best_window_match(
        normalized_alias: str,
        tokens: list[tuple[str, int, int]],
    ) -> tuple[str, float, int, int] | None:
        if not tokens:
            return None

        alias_word_count = len(
            normalized_alias.split()
        )

        minimum_length = max(
            1,
            alias_word_count - 1,
        )
        maximum_length = min(
            len(tokens),
            alias_word_count + 1,
        )

        best_match: tuple[
            str,
            float,
            int,
            int,
        ] | None = None

        for window_length in range(
            minimum_length,
            maximum_length + 1,
        ):
            for start_index in range(
                len(tokens) - window_length + 1
            ):
                window = tokens[
                    start_index:
                    start_index + window_length
                ]

                phrase = " ".join(
                    token[0]
                    for token in window
                )
                score = SequenceMatcher(
                    None,
                    phrase,
                    normalized_alias,
                ).ratio()

                candidate = (
                    phrase,
                    score,
                    window[0][1],
                    window[-1][2],
                )

                if (
                    best_match is None
                    or score > best_match[1]
                ):
                    best_match = candidate

        return best_match

    @staticmethod
    def _store_best_entity(
        entities: dict[
            tuple[EntityType, str | None],
            EntityMention,
        ],
        entity: EntityMention,
    ) -> None:
        key = (
            entity.entity_type,
            entity.uri,
        )
        existing = entities.get(key)

        if existing is None:
            entities[key] = entity
            return

        existing_length = (
            (existing.end or 0)
            - (existing.start or 0)
        )
        entity_length = (
            (entity.end or 0)
            - (entity.start or 0)
        )

        if (
            entity.confidence > existing.confidence
            or (
                entity.confidence
                == existing.confidence
                and entity_length > existing_length
            )
        ):
            entities[key] = entity

    def link(
        self,
        text: str,
    ) -> list[EntityMention]:
        normalized_text = normalize_text(text)

        if not normalized_text:
            return []

        entities: dict[
            tuple[EntityType, str | None],
            EntityMention,
        ] = {}

        for artist in self._artists:
            match = self._best_alias_match(
                normalized_text,
                self._artist_aliases(artist),
            )

            if match is None:
                continue

            mention_text, score, start, end = match

            self._store_best_entity(
                entities,
                EntityMention(
                    entity_type=EntityType.ARTIST,
                    text=mention_text,
                    canonical_name=artist.name,
                    uri=artist.uri,
                    confidence=score,
                    start=start,
                    end=end,
                ),
            )

        for artwork in self._artworks:
            match = self._best_alias_match(
                normalized_text,
                self._artwork_aliases(artwork),
            )

            if match is None:
                continue

            mention_text, score, start, end = match

            self._store_best_entity(
                entities,
                EntityMention(
                    entity_type=EntityType.ARTWORK,
                    text=mention_text,
                    canonical_name=artwork.title,
                    uri=artwork.uri,
                    confidence=score,
                    start=start,
                    end=end,
                ),
            )

        for place in self._places:
            match = self._best_alias_match(
                normalized_text,
                self._place_aliases(place),
            )

            if match is None:
                continue

            mention_text, score, start, end = match

            self._store_best_entity(
                entities,
                EntityMention(
                    entity_type=EntityType.PLACE,
                    text=mention_text,
                    canonical_name=place.name,
                    uri=place.uri,
                    confidence=score,
                    start=start,
                    end=end,
                ),
            )

        city_match = re.search(
            r"\bnapoli\b",
            normalized_text,
        )

        if city_match is not None:
            self._store_best_entity(
                entities,
                EntityMention(
                    entity_type=EntityType.CITY,
                    text=city_match.group(),
                    canonical_name="Napoli",
                    uri=None,
                    confidence=1.0,
                    start=city_match.start(),
                    end=city_match.end(),
                ),
            )

        return sorted(
            entities.values(),
            key=lambda entity: (
                entity.start
                if entity.start is not None
                else len(normalized_text),
                entity.end
                if entity.end is not None
                else len(normalized_text),
                entity.entity_type.value,
            ),
        )
