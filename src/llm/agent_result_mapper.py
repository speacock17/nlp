from typing import Any

from src.core.enums import Intent
from src.core.models import (
    Artist,
    Artwork,
    BotResponse,
    Inconsistency,
    Place,
)
from src.llm.tool_calling_agent import AgentResult


_ARTWORK_TOOLS = {
    "get_artwork_information",
    "list_artworks_by_artist",
    "list_artworks_by_place",
    "search_artworks",
}

_DEFAULT_INTENTS = {
    "get_artwork_information": Intent.ARTWORK_DESCRIPTION,
    "list_artworks_by_artist": (
        Intent.LIST_ARTWORKS_BY_ARTIST
    ),
    "list_artworks_by_place": Intent.PLACE_ARTWORKS,
    "search_artworks": Intent.ARTWORK_DESCRIPTION,
    "get_artist_information": Intent.ARTIST_INFO,
    "get_place_information": Intent.PLACE_ARTWORKS,
}


class AgentResultMapper:
    def map(
        self,
        result: AgentResult,
        preferred_intent: Intent | None = None,
        inconsistency: Inconsistency | None = None,
        needs_clarification: bool = False,
        clarification_options: list[str] | None = None,
    ) -> BotResponse:
        artworks: list[Artwork] = []
        artists: list[Artist] = []
        places: list[Place] = []

        for execution in result.executions:
            tool_name = execution.tool_call.name
            data_items = self._extract_data_items(
                execution.result
            )

            if tool_name in _ARTWORK_TOOLS:
                artworks.extend(
                    Artwork(**item)
                    for item in data_items
                )
            elif tool_name == "get_artist_information":
                artists.extend(
                    Artist(**item)
                    for item in data_items
                )
            elif tool_name == "get_place_information":
                places.extend(
                    Place(**item)
                    for item in data_items
                )

        intent = (
            preferred_intent
            if preferred_intent is not None
            else self._infer_intent(result)
        )

        return BotResponse(
            text=result.content,
            intent=intent,
            artworks=self._deduplicate_by_uri(artworks),
            artists=self._deduplicate_by_uri(artists),
            places=self._deduplicate_by_uri(places),
            inconsistency=inconsistency,
            needs_clarification=needs_clarification,
            clarification_options=list(
                clarification_options or []
            ),
        )

    @staticmethod
    def _extract_data_items(
        result: dict[str, Any],
    ) -> list[dict[str, Any]]:
        data = result.get("data")

        if data is None:
            return []

        if isinstance(data, dict):
            return [data]

        if isinstance(data, list):
            if not all(
                isinstance(item, dict)
                for item in data
            ):
                raise TypeError(
                    "I risultati dei tool devono contenere "
                    "dizionari"
                )

            return data

        raise TypeError(
            "Il campo data del risultato non ? valido"
        )

    @staticmethod
    def _infer_intent(
        result: AgentResult,
    ) -> Intent:
        if not result.executions:
            return Intent.UNKNOWN

        first_tool = (
            result.executions[0].tool_call.name
        )

        return _DEFAULT_INTENTS.get(
            first_tool,
            Intent.UNKNOWN,
        )

    @staticmethod
    def _deduplicate_by_uri(
        items: list[Any],
    ) -> list[Any]:
        unique_items = []
        seen_uris: set[str] = set()

        for item in items:
            if item.uri in seen_uris:
                continue

            seen_uris.add(item.uri)
            unique_items.append(item)

        return unique_items
