import re

from src.core.enums import ClaimType, EntityType
from src.core.models import Claim, EntityMention
from src.core.normalization import normalize_text


class ClaimExtractor:
    _AUTHOR_QUESTIONS = (
        "chi ha dipinto",
        "chi ha realizzato",
        "chi e l autore",
        "qual e l autore",
        "autore dell opera",
        "autore del dipinto",
    )

    _AUTHOR_ASSERTIONS = (
        " e di ",
        " fu dipinta da ",
        " fu dipinto da ",
        " e stata dipinta da ",
        " e stato dipinto da ",
        " realizzata da ",
        " realizzato da ",
    )

    _LOCATION_ASSERTIONS = (
        " si trova ",
        " e conservata ",
        " e conservato ",
        " e esposta ",
        " e esposto ",
        " si conserva ",
    )

    _DATE_PATTERNS = (
        r"\be del\s+(\d{4})\b",
        r"\brisale al\s+(\d{4})\b",
        r"\brisale a\s+(\d{4})\b",
        r"\bfu dipinta nel\s+(\d{4})\b",
        r"\bfu dipinto nel\s+(\d{4})\b",
        r"\be stata dipinta nel\s+(\d{4})\b",
        r"\be stato dipinto nel\s+(\d{4})\b",
    )

    @staticmethod
    def _first_entity(
        entities: list[EntityMention],
        entity_type: EntityType,
    ) -> EntityMention | None:
        return next(
            (
                entity
                for entity in entities
                if entity.entity_type == entity_type
            ),
            None,
        )

    @staticmethod
    def _contains_any(
        text: str,
        expressions: tuple[str, ...],
    ) -> bool:
        padded_text = f" {text} "

        return any(
            expression in padded_text
            for expression in expressions
        )

    @staticmethod
    def _has_author_relation(
        text: str,
        artwork: EntityMention,
        artist: EntityMention,
    ) -> bool:
        artwork_names = {
            normalize_text(artwork.text),
            normalize_text(
                artwork.canonical_name or ""
            ),
        }
        artist_names = {
            normalize_text(artist.text),
            normalize_text(
                artist.canonical_name or ""
            ),
        }

        artwork_names.discard("")
        artist_names.discard("")

        connectors = (
            "di",
            "dipinta da",
            "dipinto da",
            "realizzata da",
            "realizzato da",
            "attribuita a",
            "attribuito a",
        )

        for artwork_name in artwork_names:
            for artist_name in artist_names:
                for connector in connectors:
                    pattern = (
                        rf"\b{re.escape(artwork_name)}"
                        rf"\s+{re.escape(connector)}\s+"
                        rf"{re.escape(artist_name)}\b"
                    )

                    if re.search(pattern, text):
                        return True

        return False

    def extract(
        self,
        text: str,
        entities: list[EntityMention],
    ) -> list[Claim]:
        normalized_text = normalize_text(text)

        if not normalized_text:
            return []

        artwork = self._first_entity(
            entities,
            EntityType.ARTWORK,
        )

        if artwork is None or artwork.uri is None:
            return []

        claims: list[Claim] = []

        artist = self._first_entity(
            entities,
            EntityType.ARTIST,
        )

        is_author_question = any(
            expression in normalized_text
            for expression in self._AUTHOR_QUESTIONS
        )

        if (
            artist is not None
            and artist.canonical_name is not None
            and not is_author_question
            and (
                self._contains_any(
                    normalized_text,
                    self._AUTHOR_ASSERTIONS,
                )
                or self._has_author_relation(
                    normalized_text,
                    artwork,
                    artist,
                )
            )
        ):
            claims.append(
                Claim(
                    claim_type=ClaimType.ARTWORK_AUTHOR,
                    subject_uri=artwork.uri,
                    claimed_value=artist.canonical_name,
                    confidence=1.0,
                )
            )

        place = self._first_entity(
            entities,
            EntityType.PLACE,
        )

        if (
            place is not None
            and place.canonical_name is not None
            and self._contains_any(
                normalized_text,
                self._LOCATION_ASSERTIONS,
            )
        ):
            claims.append(
                Claim(
                    claim_type=ClaimType.ARTWORK_LOCATION,
                    subject_uri=artwork.uri,
                    claimed_value=place.canonical_name,
                    confidence=1.0,
                )
            )

        for pattern in self._DATE_PATTERNS:
            match = re.search(pattern, normalized_text)

            if match is None:
                continue

            claims.append(
                Claim(
                    claim_type=ClaimType.ARTWORK_DATE,
                    subject_uri=artwork.uri,
                    claimed_value=match.group(1),
                    confidence=1.0,
                )
            )
            break

        return claims
