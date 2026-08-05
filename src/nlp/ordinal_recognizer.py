import re

from src.core.enums import EntityType
from src.core.models import EntityMention
from src.core.normalization import normalize_text


class OrdinalRecognizer:
    _ORDINAL_VALUES = {
        "primo": "1",
        "prima": "1",
        "secondo": "2",
        "seconda": "2",
        "terzo": "3",
        "terza": "3",
        "quarto": "4",
        "quarta": "4",
        "quinto": "5",
        "quinta": "5",
        "sesto": "6",
        "sesta": "6",
        "settimo": "7",
        "settima": "7",
        "ottavo": "8",
        "ottava": "8",
        "nono": "9",
        "nona": "9",
        "decimo": "10",
        "decima": "10",
        "ultimo": "last",
        "ultima": "last",
    }

    _PATTERN = re.compile(
        r"\b("
        + "|".join(_ORDINAL_VALUES)
        + r")\b"
    )

    def recognize(
        self,
        text: str,
    ) -> list[EntityMention]:
        normalized_text = normalize_text(text)

        match = self._PATTERN.search(normalized_text)

        if match is None:
            return []

        ordinal_text = match.group(1)

        return [
            EntityMention(
                entity_type=EntityType.ORDINAL,
                text=ordinal_text,
                canonical_name=(
                    self._ORDINAL_VALUES[ordinal_text]
                ),
                uri=None,
                confidence=1.0,
                start=match.start(),
                end=match.end(),
            )
        ]
