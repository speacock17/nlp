import json
from dataclasses import asdict
from typing import Any, Callable

from src.core.interfaces import KnowledgeRepository


_ARTWORK_INFORMATION_OPTIONS = (
    "overview",
    "author",
    "location",
    "date",
    "description",
)

_ARTWORK_REQUEST_FIELDS = (
    "overview",
    "author",
    "location",
    "date",
    "medium",
    "subject",
    "description",
)

_ARTIST_REQUEST_FIELDS = (
    "overview",
    "full_name",
    "birth_date",
    "birth_place",
    "death_date",
    "death_place",
    "description",
)

_PLACE_REQUEST_FIELDS = (
    "overview",
    "city",
    "place_type",
    "address",
    "coordinates",
    "description",
)


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
                    },
                    "requested_fields": {
                        "type": "array",
                        "items": {
                            "type": "string",
                            "enum": list(
                                _ARTWORK_REQUEST_FIELDS
                            ),
                        },
                        "minItems": 1,
                        "uniqueItems": True,
                        "description": (
                            "Informazioni realmente richieste "
                            "dall'utente. Usa overview da solo "
                            "per richieste generiche come "
                            "'parlami dell'opera'. Per richieste "
                            "specifiche seleziona soltanto i campi "
                            "necessari, anche pi? di uno."
                        ),
                    },
                },
                "required": [
                    "artwork_title",
                    "requested_fields",
                ],
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
            "name": "find_artworks_by_subject",
            "description": (
                "Trova le opere visitabili nella citta richiesta "
                "che raffigurano o rappresentano il soggetto "
                "indicato dall'utente, usando le descrizioni "
                "presenti nella knowledge base."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "subject": {
                        "type": "string",
                        "description": "Soggetto raffigurato",
                    },
                    "artist_name": {
                        "type": "string",
                        "description": (
                            "Nome dell'artista, se specificato"
                        ),
                    },
                    "city": {
                        "type": "string",
                        "description": "Citta, normalmente Napoli",
                        "default": "Napoli",
                    },
                },
                "required": ["subject"],
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
            "name": "list_places",
            "description": (
                "Elenca i musei e i luoghi di Napoli "
                "in cui sono visitabili opere presenti "
                "nel database."
            ),
            "parameters": {
                "type": "object",
                "properties": {},
                "required": [],
                "additionalProperties": False,
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "list_places_with_artworks",
            "description": (
                "Elenca tutti i musei e luoghi presenti nel "
                "database insieme alle opere visitabili "
                "in ciascuno."
            ),
            "parameters": {
                "type": "object",
                "properties": {},
                "required": [],
                "additionalProperties": False,
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
                    },
                    "requested_fields": {
                        "type": "array",
                        "items": {
                            "type": "string",
                            "enum": list(
                                _ARTIST_REQUEST_FIELDS
                            ),
                        },
                        "minItems": 1,
                        "uniqueItems": True,
                        "description": (
                            "Informazioni realmente richieste "
                            "sull'artista. Usa overview da solo "
                            "per richieste generiche come "
                            "'parlami di Caravaggio'. Per domande "
                            "specifiche seleziona soltanto i "
                            "campi necessari."
                        ),
                    },
                },
                "required": [
                    "artist_name",
                    "requested_fields",
                ],
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
                    },
                    "requested_fields": {
                        "type": "array",
                        "items": {
                            "type": "string",
                            "enum": list(
                                _PLACE_REQUEST_FIELDS
                            ),
                        },
                        "minItems": 1,
                        "uniqueItems": True,
                        "description": (
                            "Informazioni realmente richieste "
                            "sul luogo. Usa overview da solo per "
                            "richieste generiche. Per domande "
                            "specifiche seleziona soltanto i "
                            "campi necessari."
                        ),
                    },
                },
                "required": [
                    "place_name",
                    "requested_fields",
                ],
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


class _SemanticArtworkFilter:
    def __init__(self, llm_client: Any) -> None:
        self._llm_client = llm_client

    def filter(
        self,
        subject: str,
        artworks: list[dict[str, str]],
    ) -> list[dict[str, Any]]:
        classifications = []

        schema = {
            "type": "object",
            "properties": {
                "matches": {
                    "type": "boolean",
                },
            },
            "required": ["matches"],
            "additionalProperties": False,
        }

        system_message = (
            "Sei un classificatore semantico rigoroso. "
            "Devi stabilire se il soggetto richiesto e "
            "realmente raffigurato nell'opera descritta. "
            "Usa esclusivamente la descrizione fornita. "
            "Il soggetto richiesto deve essere soddisfatto "
            "nella sua interezza: non basta che la descrizione "
            "raffiguri una persona o un concetto collegato. "
            "Per esempio, 'Gesu sulla croce' richiede che Gesu "
            "sia raffigurato sulla croce; una flagellazione o "
            "Gesu legato a una colonna NON corrispondono. "
            "Puoi riconoscere soltanto equivalenze semantiche "
            "chiare e pertinenti, come Gesu e Cristo. "
            "Non confondere soggetti religiosi differenti: "
            "Madonna o Vergine Maria non significa "
            "automaticamente qualsiasi scena con Gesu; "
            "Immacolata indica una specifica raffigurazione "
            "mariana; Spirito Santo o colomba non significano "
            "angelo. "
            "Una persona, un soggetto o un'opera citati "
            "soltanto come confronto, influenza, riferimento "
            "storico o altra opera NON sono raffigurati "
            "nell'opera analizzata. "
            "Rispondi true solo quando la descrizione fornisce "
            "evidenza positiva sufficiente del soggetto "
            "richiesto. In caso di dubbio rispondi false. "
            "Non usare conoscenze esterne sull'opera."
        )

        for artwork in artworks:
            response = self._llm_client.chat(
                messages=[
                    {
                        "role": "system",
                        "content": system_message,
                    },
                    {
                        "role": "user",
                        "content": json.dumps(
                            {
                                "subject": subject,
                                "description":
                                    artwork["description"],
                            },
                            ensure_ascii=False,
                        ),
                    },
                ],
                format=schema,
            )

            raw_content = response.content.strip()

            if raw_content.startswith("```"):
                lines = raw_content.splitlines()

                if lines:
                    lines = lines[1:]

                if (
                    lines
                    and lines[-1].strip() == "```"
                ):
                    lines = lines[:-1]

                raw_content = "\n".join(lines).strip()

            parsed = json.loads(raw_content)

            if not isinstance(parsed, dict):
                raise ValueError(
                    "La classificazione semantica deve "
                    "essere un oggetto JSON"
                )

            matches = parsed.get("matches")

            if not isinstance(matches, bool):
                raise ValueError(
                    "Il campo matches deve essere booleano"
                )

            classifications.append(
                {
                    "title": artwork["title"],
                    "matches": matches,
                }
            )

        return classifications


class KnowledgeToolExecutor:
    def __init__(
        self,
        knowledge_repository: KnowledgeRepository,
        semantic_llm_client: Any | None = None,
    ) -> None:
        self._knowledge_repository = knowledge_repository
        self._semantic_filter = (
            _SemanticArtworkFilter(semantic_llm_client)
            if semantic_llm_client is not None
            else None
        )

        self._handlers: dict[
            str,
            Callable[[dict[str, Any]], dict[str, Any]],
        ] = {
            "get_artwork_information":
                self._get_artwork_information,
            "list_artworks_by_artist":
                self._list_artworks_by_artist,
            "find_artworks_by_subject":
                self._find_artworks_by_subject,            "list_artworks_by_place":
                self._list_artworks_by_place,
            "list_places":
                self._list_places,
            "list_places_with_artworks":
                self._list_places_with_artworks,
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
        self._validate_requested_fields(
            arguments=arguments,
            allowed_fields=_ARTWORK_REQUEST_FIELDS,
            legacy_key="requested_information",
            legacy_allowed_fields=(
                _ARTWORK_INFORMATION_OPTIONS
            ),
        )

        artwork = (
            self._knowledge_repository
            .get_artwork_by_title(artwork_title)
        )

        if artwork is None:
            candidates = (
                self._knowledge_repository
                .search_artworks(
                    artwork_title,
                    2,
                )
            )

            if len(candidates) == 1:
                artwork = candidates[0]

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

    def _find_artworks_by_subject(
        self,
        arguments: dict[str, Any],
    ) -> dict[str, Any]:
        subject = self._required_string(
            arguments,
            "subject",
        )
        artist_name_value = arguments.get("artist_name")

        if artist_name_value is None:
            artist_name = ""
        elif isinstance(artist_name_value, str):
            artist_name = artist_name_value.strip()
        else:
            raise TypeError(
                "artist_name deve essere una stringa"
            )
        city = self._optional_string(
            arguments,
            "city",
            default="Napoli",
        )

        if artist_name:
            artworks = (
                self._knowledge_repository
                .list_artworks_by_artist(
                    artist_name,
                    city,
                )
            )
        else:
            places = (
                self._knowledge_repository
                .list_places()
            )

            artworks_by_uri = {}

            for place in places:
                if place.city.strip().casefold() != city.casefold():
                    continue

                place_artworks = (
                    self._knowledge_repository
                    .list_artworks_by_place(
                        place.name
                    )
                )

                for artwork in place_artworks:
                    if (
                        isinstance(artwork.city, str)
                        and artwork.city.strip().casefold()
                        == city.casefold()
                    ):
                        artworks_by_uri[artwork.uri] = artwork

            artworks = list(artworks_by_uri.values())

        candidates = [
            artwork
            for artwork in artworks
            if (
                isinstance(artwork.description, str)
                and artwork.description.strip()
            )
        ]

        if not candidates or self._semantic_filter is None:
            result = self._list_result([])
            result["found"] = False
            return result

        semantic_input = [
            {
                "title": artwork.title,
                "description": artwork.description,
            }
            for artwork in candidates
        ]

        try:
            classifications = self._semantic_filter.filter(
                subject=subject,
                artworks=semantic_input,
            )
        except (TypeError, ValueError):
            result = self._list_result([])
            result["found"] = False
            return result

        candidates_by_title = {
            artwork.title.strip().casefold(): artwork
            for artwork in candidates
        }

        matched = []
        seen_titles = set()

        for classification in classifications:
            if not isinstance(classification, dict):
                continue

            title = classification.get("title")
            matches = classification.get("matches")

            if (
                not isinstance(title, str)
                or not isinstance(matches, bool)
                or not matches
            ):
                continue

            normalized_title = title.strip().casefold()
            artwork = candidates_by_title.get(normalized_title)

            if (
                artwork is not None
                and normalized_title not in seen_titles
            ):
                matched.append(artwork)
                seen_titles.add(normalized_title)

        result = self._list_result(matched)
        result["found"] = bool(matched)
        return result

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

    def _list_places(
        self,
        arguments: dict[str, Any],
    ) -> dict[str, Any]:
        places = (
            self._knowledge_repository
            .list_places()
        )

        return self._list_result(places)

    def _list_places_with_artworks(
        self,
        arguments: dict[str, Any],
    ) -> dict[str, Any]:
        places = (
            self._knowledge_repository
            .list_places()
        )

        artworks = []

        for place in places:
            artworks.extend(
                self._knowledge_repository
                .list_artworks_by_place(
                    place.name
                )
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

        self._validate_requested_fields(
            arguments=arguments,
            allowed_fields=_ARTIST_REQUEST_FIELDS,
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

        self._validate_requested_fields(
            arguments=arguments,
            allowed_fields=_PLACE_REQUEST_FIELDS,
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
    def _validate_requested_fields(
        arguments: dict[str, Any],
        allowed_fields: tuple[str, ...],
        legacy_key: str | None = None,
        legacy_allowed_fields: tuple[str, ...] | None = None,
    ) -> tuple[str, ...]:
        if "requested_fields" in arguments:
            value = arguments["requested_fields"]

            if not isinstance(value, list):
                raise TypeError(
                    "requested_fields deve essere una lista"
                )

            if not value:
                raise ValueError(
                    "requested_fields non pu? essere vuoto"
                )

            normalized_fields = []

            for field_name in value:
                if not isinstance(field_name, str):
                    raise TypeError(
                        "Ogni elemento di requested_fields "
                        "deve essere una stringa"
                    )

                normalized_field = (
                    field_name.strip().casefold()
                )

                if not normalized_field:
                    raise ValueError(
                        "requested_fields non pu? contenere "
                        "valori vuoti"
                    )

                if normalized_field not in allowed_fields:
                    raise ValueError(
                        "requested_fields contiene un valore "
                        "non consentito: "
                        f"{field_name}"
                    )

                if normalized_field in normalized_fields:
                    raise ValueError(
                        "requested_fields non pu? contenere "
                        "duplicati"
                    )

                normalized_fields.append(
                    normalized_field
                )

            if (
                "overview" in normalized_fields
                and len(normalized_fields) > 1
            ):
                raise ValueError(
                    "overview deve essere usato da solo"
                )

            return tuple(normalized_fields)

        if legacy_key is not None and legacy_key in arguments:
            legacy_value = arguments[legacy_key]

            if not isinstance(legacy_value, str):
                raise TypeError(
                    f"{legacy_key} deve essere una stringa"
                )

            normalized_legacy = (
                legacy_value.strip().casefold()
            )

            allowed_legacy = (
                legacy_allowed_fields
                if legacy_allowed_fields is not None
                else allowed_fields
            )

            if normalized_legacy not in allowed_legacy:
                raise ValueError(
                    f"{legacy_key} deve essere uno dei "
                    "valori consentiti: "
                    + ", ".join(allowed_legacy)
                )

            return (normalized_legacy,)

        # Compatibilit? con chiamate interne precedenti:
        # in assenza del nuovo argomento, la richiesta
        # viene trattata come panoramica generale.
        return ("overview",)

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
