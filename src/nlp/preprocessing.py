from src.core.normalization import normalize_text


def preprocess_question(text: str) -> str:
    if not isinstance(text, str):
        raise TypeError(
            "La domanda deve essere una stringa"
        )

    return normalize_text(text)
