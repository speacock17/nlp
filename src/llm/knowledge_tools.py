from dataclasses import asdict
from typing import Any, Callable

from src.core.interfaces import KnowledgeRepository


KNOWLEDGE_TOOL_SCHEMAS = [
    {
        "type": "function",
        "function": {
            "name": "get_artwork_information",
            "description": (
                "Recupera dal database tutte le informazioni "
                "disponibili su una specifica opera."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "artwork_title": {
                        "type": "string",
                        "description": "Titolo dell'opera",
                    }
                },
                "required": ["artwork_title"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "list_artworks_by_artist",
            "description": (
                "Elenca le opere di un artista visitabili "
                "nella citt? richiesta."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "artist_name": {
                        "type": "string",
                        "description": "Nome dell'artista",
                    },
                    "city": {
                        "type": "string",
                        "description": "Citt?, normalmente Napoli",
                        "default": "Napoli",
                    },
                },
                "required": ["artist_name"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "list_artworks_by_place",
            "description": (
                "Elenca le opere presenti in uno specifico "
                "museo o luogo."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "place_name": {
                        "type": "string",
                        "description": "Nome del luogo o museo",
                    }
                },
                "required": ["place_name"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_artist_information",
            "description": (
                "Recupera dal database le informazioni "
                "disponibili su un artista."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "artist_name": {
                        "type": "string",
                        "description": "Nome dell'artista",
                    }
                },
                "required": ["artist_name"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_place_information",
            "description": (
                "Recupera dal database le informazioni "
                "disponibili su un museo o luogo."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "place_name": {
                        "type": "string",
                        "description": "Nome del luogo o museo",
                    }
                },
                "required": ["place_name"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "search_artworks",
            "description": (
                "Cerca opere nel database quando il titolo "
                "fornito ? incompleto, approssimativo o incerto."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": (
                            "Testo o parte del titolo da cercare"
                        ),
                    },
                    "limit": {
                        "type": "integer",
                        "description": (
                            "Numero massimo di risultati"
                        ),
                        "default": 5,
                        "minimum": 1,
                        "maximum": 10,
                    },
                },
                "required": ["query"],
            },
        },
    },
]


class KnowledgeToolExecutor:
    def __init__(
        self,
        knowledge_repository: KnowledgeRepository,
    ) -> None:
        self._knowledge_repository = knowledge_repository

        self._handlers: dict[
            str,
            Callable[[dict[str, Any]], dict[str, Any]],
        ] = {
            "get_artwork_information":
                self._get_artwork_information,
            "list_artworks_by_artist":
                self._list_artworks_by_artist,
            "list_artworks_by_place":
                self._list_artworks_by_place,
            "get_artist_information":
                self._get_artist_information,
            "get_place_information":
                self._get_place_information,
            "search_artworks":
                self._search_artworks,
        }

    def execute(
        self,
        name: str,
        arguments: dict[str, Any],
    ) -> dict[str, Any]:
        handler = self._handlers.get(name)

        if handler is None:
            raise ValueError(
                f"Tool non autorizzato: {name}"
            )

        if not isinstance(arguments, dict):
            raise TypeError(
                "Gli argomenti del tool devono essere "
                "un dizionario"
            )

        return handler(arguments)

    def _get_artwork_information(
        self,
        arguments: dict[str, Any],
    ) -> dict[str, Any]:
        artwork_title = self._required_string(
            arguments,
            "artwork_title",
        )

        artwork = (
            self._knowledge_repository
            .get_artwork_by_title(artwork_title)
        )

        return self._single_result(artwork)

    def _list_artworks_by_artist(
        self,
        arguments: dict[str, Any],
    ) -> dict[str, Any]:
        artist_name = self._required_string(
            arguments,
            "artist_name",
        )
        city = self._optional_string(
            arguments,
            "city",
            default="Napoli",
        )

        artworks = (
            self._knowledge_repository
            .list_artworks_by_artist(
                artist_name,
                city,
            )
        )

        return self._list_result(artworks)

    def _list_artworks_by_place(
        self,
        arguments: dict[str, Any],
    ) -> dict[str, Any]:
        place_name = self._required_string(
            arguments,
            "place_name",
        )

        artworks = (
            self._knowledge_repository
            .list_artworks_by_place(place_name)
        )

        return self._list_result(artworks)

    def _get_artist_information(
        self,
        arguments: dict[str, Any],
    ) -> dict[str, Any]:
        artist_name = self._required_string(
            arguments,
            "artist_name",
        )

        artist = (
            self._knowledge_repository
            .get_artist_by_name(artist_name)
        )

        return self._single_result(artist)

    def _get_place_information(
        self,
        arguments: dict[str, Any],
    ) -> dict[str, Any]:
        place_name = self._required_string(
            arguments,
            "place_name",
        )

        place = (
            self._knowledge_repository
            .get_place_by_name(place_name)
        )

        return self._single_result(place)

    def _search_artworks(
        self,
        arguments: dict[str, Any],
    ) -> dict[str, Any]:
        query = self._required_string(
            arguments,
            "query",
        )
        limit = arguments.get("limit", 5)

        if not isinstance(limit, int):
            raise TypeError(
                "Il limite deve essere un intero"
            )

        if not 1 <= limit <= 10:
            raise ValueError(
                "Il limite deve essere compreso tra 1 e 10"
            )

        artworks = (
            self._knowledge_repository
            .search_artworks(
                query,
                limit,
            )
        )

        return self._list_result(artworks)

    @staticmethod
    def _single_result(item: Any) -> dict[str, Any]:
        if item is None:
            return {
                "found": False,
                "data": None,
            }

        return {
            "found": True,
            "data": asdict(item),
        }

    @staticmethod
    def _list_result(
        items: list[Any],
    ) -> dict[str, Any]:
        return {
            "count": len(items),
            "data": [
                asdict(item)
                for item in items
            ],
        }

    @staticmethod
    def _required_string(
        arguments: dict[str, Any],
        key: str,
    ) -> str:
        value = arguments.get(key)

        if not isinstance(value, str):
            raise TypeError(
                f"{key} deve essere una stringa"
            )

        clean_value = value.strip()

        if not clean_value:
            raise ValueError(
                f"{key} non pu? essere vuoto"
            )

        return clean_value

    @classmethod
    def _optional_string(
        cls,
        arguments: dict[str, Any],
        key: str,
        default: str,
    ) -> str:
        value = arguments.get(key, default)

        return cls._required_string(
            {key: value},
            key,
        )
