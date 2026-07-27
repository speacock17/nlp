import re
import unicodedata


def normalize_text(text: str) -> str:
    normalized = text.casefold()
    normalized = normalized.replace("’", "'").replace("`", "'")

    normalized = unicodedata.normalize("NFKD", normalized)
    normalized = "".join(
        character
        for character in normalized
        if not unicodedata.combining(character)
    )

    normalized = normalized.replace("'", " ")
    normalized = re.sub(r"[^a-z0-9\s]", " ", normalized)
    normalized = re.sub(r"\s+", " ", normalized)

    return normalized.strip()
