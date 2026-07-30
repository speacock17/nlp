from typing import Any

from src.core.normalization import normalize_text
from src.llm.ollama_llm_client import LLMToolCall


_CARAVAGGIO_ALIASES = {
    "caravaggio",
    "merisi",
    "michelangelo merisi",
    "michelangelo merisi da caravaggio",
}

_NAPLES_NAMES = {
    "napoli",
    "naples",
}


class DomainToolCallNormalizer:
    def normalize(
        self,
        user_text: str,
        tool_call: LLMToolCall,
    ) -> LLMToolCall:
        if not isinstance(user_text, str):
            raise TypeError(
                "Il testo dell'utente deve essere "
                "una stringa"
            )

        if not isinstance(tool_call, LLMToolCall):
            raise TypeError(
                "La chiamata deve essere un LLMToolCall"
            )

        arguments = dict(tool_call.arguments)
        tool_name = tool_call.name

        artist_name = arguments.get("artist_name")

        if self._is_caravaggio_alias(artist_name):
            arguments["artist_name"] = "Caravaggio"

        if self._is_naples_place_request(
            user_text=user_text,
            tool_name=tool_name,
            arguments=arguments,
        ):
            return LLMToolCall(
                name="list_artworks_by_artist",
                arguments={
                    "artist_name": "Caravaggio",
                    "city": "Napoli",
                },
            )

        return LLMToolCall(
            name=tool_name,
            arguments=arguments,
        )

    @staticmethod
    def _is_caravaggio_alias(
        value: Any,
    ) -> bool:
        if not isinstance(value, str):
            return False

        normalized_value = normalize_text(value)

        return normalized_value in _CARAVAGGIO_ALIASES

    @classmethod
    def _mentions_caravaggio(
        cls,
        user_text: str,
    ) -> bool:
        normalized_text = normalize_text(user_text)

        return any(
            alias in normalized_text
            for alias in _CARAVAGGIO_ALIASES
        )

    @classmethod
    def _is_naples_place_request(
        cls,
        user_text: str,
        tool_name: str,
        arguments: dict[str, Any],
    ) -> bool:
        if tool_name != "list_artworks_by_place":
            return False

        place_name = arguments.get("place_name")

        if not isinstance(place_name, str):
            return False

        normalized_place = normalize_text(place_name)

        return (
            normalized_place in _NAPLES_NAMES
            and cls._mentions_caravaggio(user_text)
        )
