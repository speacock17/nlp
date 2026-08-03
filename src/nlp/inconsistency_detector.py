from src.core.enums import (
    ClaimType,
    InconsistencyType,
)
from src.core.interfaces import KnowledgeRepository
from src.core.models import Claim, Inconsistency
from src.core.normalization import normalize_text


class InconsistencyDetector:
    def __init__(
        self,
        knowledge_repository: KnowledgeRepository,
    ) -> None:
        self._knowledge_repository = knowledge_repository

    def detect(
        self,
        claims: list[Claim],
    ) -> Inconsistency | None:
        for claim in claims:
            inconsistency = self._detect_claim(claim)

            if inconsistency is not None:
                return inconsistency

        return None

    def _detect_claim(
        self,
        claim: Claim,
    ) -> Inconsistency | None:
        if claim.subject_uri is None:
            return Inconsistency(
                inconsistency_type=(
                    InconsistencyType.ENTITY_NOT_FOUND
                ),
                message=(
                    "Non è stato possibile identificare "
                    "l'opera a cui si riferisce "
                    "l'affermazione."
                ),
                claimed_value=None,
                correct_value=None,
            )

        artwork = (
            self._knowledge_repository
            .get_artwork_by_uri(claim.subject_uri)
        )

        if artwork is None:
            return Inconsistency(
                inconsistency_type=(
                    InconsistencyType.ENTITY_NOT_FOUND
                ),
                message=(
                    "L'opera indicata non è presente "
                    "nella base di conoscenza."
                ),
                claimed_value=claim.subject_uri,
                correct_value=None,
            )

        if claim.claim_type == ClaimType.ARTWORK_AUTHOR:
            if self._same_text(
                claim.claimed_value,
                artwork.artist_name,
            ):
                return None

            return Inconsistency(
                inconsistency_type=(
                    InconsistencyType.WRONG_AUTHOR
                ),
                message=(
                    f"L'autore indicato non è corretto: "
                    f"{artwork.title} è attribuita a "
                    f"{artwork.artist_name}."
                ),
                claimed_value=claim.claimed_value,
                correct_value=artwork.artist_name,
            )

        if claim.claim_type == ClaimType.ARTWORK_LOCATION:
            if artwork.place_name is None:
                return None

            if self._same_text(
                claim.claimed_value,
                artwork.place_name,
            ):
                return None

            return Inconsistency(
                inconsistency_type=(
                    InconsistencyType.WRONG_LOCATION
                ),
                message=(
                    f"Il luogo indicato non è corretto: "
                    f"{artwork.title} si trova presso "
                    f"{artwork.place_name}."
                ),
                claimed_value=claim.claimed_value,
                correct_value=artwork.place_name,
            )

        if claim.claim_type == ClaimType.ARTWORK_DATE:
            if artwork.year is None:
                return None

            correct_year = str(artwork.year)

            if claim.claimed_value == correct_year:
                return None

            return Inconsistency(
                inconsistency_type=(
                    InconsistencyType.IMPOSSIBLE_DATE
                ),
                message=(
                    f"La data indicata non è corretta: "
                    f"{artwork.title} risale al "
                    f"{correct_year}."
                ),
                claimed_value=claim.claimed_value,
                correct_value=correct_year,
            )

        return None

    @staticmethod
    def _same_text(
        first_value: str,
        second_value: str,
    ) -> bool:
        return (
            normalize_text(first_value)
            == normalize_text(second_value)
        )
