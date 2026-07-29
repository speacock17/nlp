from difflib import SequenceMatcher

from src.core.constants import (
    FUZZY_MATCH_ACCEPTED_THRESHOLD,
    FUZZY_MATCH_AMBIGUOUS_THRESHOLD,
)
from src.core.normalization import normalize_text


def fuzzy_similarity(
    first_text: str,
    second_text: str,
) -> float:
    normalized_first = normalize_text(first_text)
    normalized_second = normalize_text(second_text)

    if not normalized_first or not normalized_second:
        return 0.0

    if normalized_first == normalized_second:
        return 1.0

    if (
        normalized_first in normalized_second
        or normalized_second in normalized_first
    ):
        return 1.0

    return SequenceMatcher(
        None,
        normalized_first,
        normalized_second,
    ).ratio()


def is_accepted_match(score: float) -> bool:
    return score >= FUZZY_MATCH_ACCEPTED_THRESHOLD


def is_ambiguous_match(score: float) -> bool:
    return (
        FUZZY_MATCH_AMBIGUOUS_THRESHOLD
        <= score
        < FUZZY_MATCH_ACCEPTED_THRESHOLD
    )
