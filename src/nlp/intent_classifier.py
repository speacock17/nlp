from src.core.enums import Intent
from src.nlp.preprocessing import preprocess_question


def _contains_any(
    text: str,
    expressions: tuple[str, ...],
) -> bool:
    return any(
        expression in text
        for expression in expressions
    )


def classify_intent(
    text: str,
) -> tuple[Intent, float]:
    normalized_text = preprocess_question(text)

    if not normalized_text:
        return Intent.UNKNOWN, 0.0

    if _contains_any(
        normalized_text,
        (
            "confronta",
            "confronto tra",
            "differenze tra",
            "differenza tra",
            "paragona",
        ),
    ):
        return Intent.COMPARE_ARTISTS, 0.95

    if _contains_any(
        normalized_text,
        (
            "che tempo",
            "meteo",
            "calcio",
            "partita",
            "ristorante",
            "politica",
        ),
    ):
        return Intent.OUT_OF_SCOPE, 0.95

    if _contains_any(
        normalized_text,
        (
            "e le altre",
            "e gli altri",
            "e l altra",
            "e l altro",
            "dimmi di piu",
            "continua",
            "quella",
            "quello",
            "quest opera",
        ),
    ) and len(normalized_text.split()) <= 5:
        return Intent.FOLLOW_UP, 0.85

    if _contains_any(
        normalized_text,
        (
            "quali opere si trovano",
            "quali opere ci sono",
            "opere conservate",
            "opere esposte",
            "opere presenti",
        ),
    ):
        return Intent.PLACE_ARTWORKS, 0.95

    if _contains_any(
        normalized_text,
        (
            "quali opere di",
            "opere di caravaggio",
            "opere di battistello",
            "opere di caracciolo",
            "dipinti di caravaggio",
            "dipinti di battistello",
        ),
    ):
        return Intent.LIST_ARTWORKS_BY_ARTIST, 0.95

    if _contains_any(
        normalized_text,
        (
            "dove si trova",
            "dove e situata",
            "dove e situato",
            "dov e situata",
            "dov e situato",
            "dove e conservata",
            "dove e conservato",
            "dov e conservata",
            "dov e conservato",
            "in quale museo",
            "in quale chiesa",
            "luogo si trova",
        ),
    ):
        return Intent.ARTWORK_LOCATION, 0.95

    if _contains_any(
        normalized_text,
        (
            "chi ha dipinto",
            "chi ha realizzato",
            "chi e l autore",
            "autore dell opera",
            "autore del dipinto",
        ),
    ):
        return Intent.ARTWORK_AUTHOR, 0.95

    if _contains_any(
        normalized_text,
        (
            "in che anno",
            "quando e stata dipinta",
            "quando e stato dipinto",
            "quando fu dipinta",
            "quando fu realizzata",
            "data dell opera",
        ),
    ):
        return Intent.ARTWORK_DATE, 0.95

    if _contains_any(
        normalized_text,
        (
            "descrivimi",
            "descrivi",
            "parlami dell opera",
            "parlami del dipinto",
            "cosa rappresenta",
            "informazioni sull opera",
        ),
    ):
        return Intent.ARTWORK_DESCRIPTION, 0.90

    if _contains_any(
        normalized_text,
        (
            "chi era",
            "chi e caravaggio",
            "chi e battistello",
            "parlami di caravaggio",
            "parlami di battistello",
            "informazioni su caravaggio",
            "informazioni su battistello",
            "biografia",
        ),
    ):
        return Intent.ARTIST_INFO, 0.90

    return Intent.UNKNOWN, 0.20
