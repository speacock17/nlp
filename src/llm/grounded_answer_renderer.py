from typing import Any

from src.llm.tool_calling_agent import ToolExecution


class GroundedAnswerRenderer:
    def render(
        self,
        executions: list[ToolExecution],
    ) -> str:
        if not executions:
            return (
                "Posso rispondere soltanto sulle opere di "
                "Caravaggio e Battistello Caracciolo "
                "visitabili a Napoli."
            )

        sections = [
            self._render_execution(execution)
            for execution in executions
        ]

        return " ".join(
            section
            for section in sections
            if section
        ).strip()

    def _render_execution(
        self,
        execution: ToolExecution,
    ) -> str:
        tool_name = execution.tool_call.name

        handlers = {
            "list_artworks_by_artist":
                self._render_artworks_by_artist,
            "find_artworks_by_subject":
                self._render_artworks_by_subject,
            "list_artworks_by_place":
                self._render_artworks_by_place,
            "list_places":
                self._render_places,
            "list_places_with_artworks":
                self._render_places_with_artworks,
            "search_artworks":
                self._render_artwork_search,
            "get_artwork_information":
                self._render_artwork_information,
            "get_artist_information":
                self._render_artist_information,
            "get_place_information":
                self._render_place_information,
        }

        handler = handlers.get(tool_name)

        if handler is None:
            raise ValueError(
                f"Tool non supportato dal renderer: "
                f"{tool_name}"
            )

        return handler(
            execution.tool_call.arguments,
            execution.result,
        )

    def _render_artworks_by_artist(
        self,
        arguments: dict[str, Any],
        result: dict[str, Any],
    ) -> str:
        artist_name = self._text(
            arguments.get("artist_name")
        )
        city = self._text(
            arguments.get("city")
        ) or "Napoli"
        artworks = self._data_list(result)

        if not artworks:
            return (
                f"Non ho trovato nel database opere di "
                f"{artist_name or 'questo artista'} "
                f"visitabili a {city}."
            )

        introduction = (
            f"Nel database risultano "
            f"{len(artworks)} opere"
        )

        if artist_name:
            introduction += f" di {artist_name}"

        if city:
            introduction += f" visitabili a {city}"

        details = [
            self._artwork_location_sentence(artwork)
            for artwork in artworks
        ]

        return (
            introduction
            + ": "
            + "; ".join(details)
            + "."
        )

    def _render_artworks_by_subject(
        self,
        arguments: dict[str, Any],
        result: dict[str, Any],
    ) -> str:
        subject = self._text(
            arguments.get("subject")
        )
        artist_name = self._text(
            arguments.get("artist_name")
        )
        artworks = self._data_list(result)

        if not artworks:
            if artist_name:
                return (
                    f"Non ho trovato nel database opere di "
                    f"{artist_name} che raffigurano "
                    f"{subject or 'questo soggetto'}."
                )

            return (
                f"Non ho trovato nel database opere che "
                f"raffigurano "
                f"{subject or 'questo soggetto'}."
            )

        introduction = (
            f"Nel database risultano {len(artworks)} opere"
        )

        if artist_name:
            introduction += f" di {artist_name}"

        introduction += (
            f" che raffigurano "
            f"{subject or 'il soggetto richiesto'}"
        )

        details = [
            self._artwork_location_sentence(artwork)
            for artwork in artworks
        ]

        return (
            introduction
            + ": "
            + "; ".join(details)
            + "."
        )
    def _render_artworks_by_place(
        self,
        arguments: dict[str, Any],
        result: dict[str, Any],
    ) -> str:
        place_name = self._text(
            arguments.get("place_name")
        )
        artworks = self._data_list(result)

        if not artworks:
            return (
                f"Non ho trovato nel database opere "
                f"associate a "
                f"{place_name or 'questo luogo'}."
            )

        titles = [
            self._text(artwork.get("title"))
            or "Opera senza titolo"
            for artwork in artworks
        ]

        return (
            f"Presso {place_name or 'questo luogo'} "
            f"risultano: "
            + "; ".join(titles)
            + "."
        )

    def _render_places_with_artworks(
        self,
        arguments: dict[str, Any],
        result: dict[str, Any],
    ) -> str:
        artworks = self._data_list(result)

        if not artworks:
            return (
                "Non risultano opere associate ai luoghi "
                "presenti nel database."
            )

        grouped: dict[str, list[str]] = {}

        for artwork in artworks:
            place_name = (
                self._text(
                    artwork.get("place_name")
                )
                or "Luogo non specificato"
            )
            title = (
                self._text(
                    artwork.get("title")
                )
                or "Opera senza titolo"
            )

            grouped.setdefault(
                place_name,
                [],
            ).append(title)

        details = [
            (
                f"{place_name}: "
                + "; ".join(titles)
            )
            for place_name, titles
            in grouped.items()
        ]

        return (
            "Nei luoghi presenti nel database puoi vedere: "
            + ". ".join(details)
            + "."
        )

    def _render_places(
        self,
        arguments: dict[str, Any],
        result: dict[str, Any],
    ) -> str:
        places = self._data_list(result)

        if not places:
            return (
                "Non risultano luoghi visitabili "
                "nel database."
            )

        names = [
            self._text(place.get("name"))
            or "Luogo senza nome"
            for place in places
        ]

        return (
            "Le opere presenti nel database sono "
            "visitabili presso: "
            + ", ".join(names)
            + "."
        )

    def _render_artwork_search(
        self,
        arguments: dict[str, Any],
        result: dict[str, Any],
    ) -> str:
        query = self._text(
            arguments.get("query")
        )
        artworks = self._data_list(result)

        if not artworks:
            return (
                f"Non ho trovato nel database opere "
                f"corrispondenti a "
                f"{query or 'questa ricerca'}."
            )

        details = [
            self._artwork_location_sentence(artwork)
            for artwork in artworks
        ]

        return (
            "Ho trovato: "
            + "; ".join(details)
            + "."
        )

    def _render_artwork_information(
        self,
        arguments: dict[str, Any],
        result: dict[str, Any],
    ) -> str:
        artwork = self._single_data(result)

        if artwork is None:
            title = self._text(
                arguments.get("artwork_title")
            )

            return (
                f"Non ho trovato nel database "
                f"informazioni su "
                f"{title or 'questa opera'}."
            )

        title = (
            self._text(artwork.get("title"))
            or "L'opera"
        )

        artist_name = self._text(
            artwork.get("artist_name")
        )
        place_name = self._text(
            artwork.get("place_name")
        )
        year = artwork.get("year")
        completion_date = self._text(
            artwork.get("completion_date")
        )
        medium = self._text(
            artwork.get("medium")
        )
        subject = self._text(
            artwork.get("subject")
        )
        raw_description = artwork.get(
            "description"
        )
        description = self._text(
            raw_description
        )

        requested_fields = self._requested_fields(
            arguments=arguments,
            legacy_key="requested_information",
        )

        if requested_fields == ("overview",):
            facts = []

            if artist_name:
                facts.append(
                    f"è attribuita a {artist_name}"
                )

            if place_name:
                facts.append(
                    f"si trova presso {place_name}"
                )

            if year is not None:
                facts.append(
                    f"è datata {year}"
                )
            elif completion_date:
                facts.append(
                    f"ha data di completamento "
                    f"{completion_date}"
                )

            if medium:
                facts.append(
                    f"la tecnica indicata è {medium}"
                )

            if description:
                description_text = description.strip()
                first_sentence = description_text.partition(".")[0].strip()

                if first_sentence:
                    facts.append(first_sentence)

            if not facts:
                return (
                    f"Nel database è presente {title}, "
                    f"ma non risultano altri dettagli."
                )

            return (
                f"{title}: "
                + "; ".join(facts)
                + "."
            )

        if requested_fields == ("author",):
            if artist_name:
                return (
                    f"{title} "
                    f"è attribuita a {artist_name}."
                )

            return (
                f"Nel database non è disponibile "
                f"l'autore di {title}."
            )

        if requested_fields == ("location",):
            if place_name:
                return (
                    f"{title} si trova presso "
                    f"{place_name}."
                )

            return (
                f"Nel database non è disponibile "
                f"il luogo in cui si trova {title}."
            )

        if requested_fields == ("date",):
            if year is not None:
                return (
                    f"{title} è stato realizzato "
                    f"nel {year}."
                )

            if completion_date:
                return (
                    f"{title} ha data di completamento "
                    f"{completion_date}."
                )

            return (
                f"Nel database non è disponibile "
                f"la data di realizzazione di {title}."
            )

        if requested_fields == ("description",):
            if isinstance(raw_description, str):
                return raw_description

            return (
                f"Nel database non è disponibile "
                f"una descrizione di {title}."
            )

        if requested_fields == ("medium",):
            if medium:
                return (
                    f"La tecnica indicata per {title} "
                    f"è {medium}."
                )

            return (
                f"Nel database non è disponibile "
                f"la tecnica di {title}."
            )

        if requested_fields == ("subject",):
            if subject:
                return (
                    f"Il soggetto indicato per {title} "
                    f"è {subject}."
                )

            return (
                f"Nel database non è disponibile "
                f"il soggetto di {title}."
            )

        facts = []

        for field_name in requested_fields:
            if field_name == "author" and artist_name:
                facts.append(
                    f"è attribuita a {artist_name}"
                )

            elif (
                field_name == "location"
                and place_name
            ):
                facts.append(
                    f"si trova presso {place_name}"
                )

            elif field_name == "date":
                if year is not None:
                    facts.append(
                        f"è stata realizzata nel {year}"
                    )
                elif completion_date:
                    facts.append(
                        f"ha data di completamento "
                        f"{completion_date}"
                    )

            elif field_name == "medium" and medium:
                facts.append(
                    f"la tecnica indicata è {medium}"
                )

            elif field_name == "subject" and subject:
                facts.append(
                    f"il soggetto indicato è {subject}"
                )

            elif (
                field_name == "description"
                and description
            ):
                facts.append(
                    description.rstrip(".")
                )

        if not facts:
            return (
                f"Nel database non sono disponibili "
                f"le informazioni richieste su {title}."
            )

        return (
            f"{title}: "
            + "; ".join(facts)
            + "."
        )

    def _render_artist_information(
        self,
        arguments: dict[str, Any],
        result: dict[str, Any],
    ) -> str:
        artist = self._single_data(result)

        if artist is None:
            name = self._text(
                arguments.get("artist_name")
            )

            return (
                f"Non ho trovato nel database "
                f"informazioni su "
                f"{name or 'questo artista'}."
            )

        name = (
            self._text(artist.get("name"))
            or "L'artista"
        )

        full_name = self._text(
            artist.get("full_name")
        )
        birth_date = self._text(
            artist.get("birth_date")
        )
        death_date = self._text(
            artist.get("death_date")
        )
        birth_place = self._text(
            artist.get("birth_place")
        )
        death_place = self._text(
            artist.get("death_place")
        )
        description = self._text(
            artist.get("description")
        )

        requested_fields = self._requested_fields(
            arguments
        )

        if requested_fields == ("birth_date",):
            if birth_date:
                return (
                    f"{name} nacque il {birth_date}."
                )

            return (
                f"Nel database non è disponibile "
                f"la data di nascita di {name}."
            )

        if requested_fields == ("birth_place",):
            if birth_place:
                return (
                    f"{name} nacque a {birth_place}."
                )

            return (
                f"Nel database non è disponibile "
                f"il luogo di nascita di {name}."
            )

        if requested_fields == ("death_date",):
            if death_date:
                return (
                    f"{name} morì il {death_date}."
                )

            return (
                f"Nel database non è disponibile "
                f"la data di morte di {name}."
            )

        if requested_fields == ("death_place",):
            if death_place:
                return (
                    f"{name} morì a {death_place}."
                )

            return (
                f"Nel database non è disponibile "
                f"il luogo di morte di {name}."
            )

        if requested_fields == ("full_name",):
            if full_name:
                return (
                    f"Il nome completo di {name} "
                    f"è {full_name}."
                )

            return (
                f"Nel database non è disponibile "
                f"il nome completo di {name}."
            )

        if requested_fields == ("description",):
            if description:
                return description

            return (
                f"Nel database non è disponibile "
                f"una descrizione di {name}."
            )

        if requested_fields == (
            "birth_date",
            "birth_place",
        ):
            if birth_date and birth_place:
                return (
                    f"{name} nacque il {birth_date} "
                    f"a {birth_place}."
                )

        facts = []

        fields_to_render = (
            (
                "full_name",
                (
                    f"il nome completo è {full_name}"
                    if full_name
                    else None
                ),
            ),
            (
                "birth_date",
                (
                    f"nacque il {birth_date}"
                    if birth_date
                    else None
                ),
            ),
            (
                "birth_place",
                (
                    f"il luogo di nascita è "
                    f"{birth_place}"
                    if birth_place
                    else None
                ),
            ),
            (
                "death_date",
                (
                    f"morì il {death_date}"
                    if death_date
                    else None
                ),
            ),
            (
                "death_place",
                (
                    f"il luogo di morte è "
                    f"{death_place}"
                    if death_place
                    else None
                ),
            ),
            (
                "description",
                (
                    description.rstrip(".")
                    if description
                    else None
                ),
            ),
        )

        if requested_fields == ("overview",):
            selected_fields = {
                "full_name",
                "birth_date",
                "birth_place",
                "death_date",
                "death_place",
                "description",
            }
        else:
            selected_fields = set(
                requested_fields
            )

        for field_name, fact in fields_to_render:
            if (
                field_name in selected_fields
                and fact
            ):
                facts.append(fact)

        if not facts:
            return (
                f"Nel database è presente {name}, "
                f"ma non risultano i dettagli richiesti."
            )

        return (
            f"{name}: "
            + "; ".join(facts)
            + "."
        )

    def _render_place_information(
        self,
        arguments: dict[str, Any],
        result: dict[str, Any],
    ) -> str:
        place = self._single_data(result)

        if place is None:
            name = self._text(
                arguments.get("place_name")
            )

            return (
                f"Non ho trovato nel database "
                f"informazioni su "
                f"{name or 'questo luogo'}."
            )

        name = (
            self._text(place.get("name"))
            or "Il luogo"
        )

        city = self._text(
            place.get("city")
        )
        place_type = self._text(
            place.get("place_type")
        )
        address = self._text(
            place.get("address")
        )
        description = self._text(
            place.get("description")
        )
        latitude = place.get("latitude")
        longitude = place.get("longitude")

        requested_fields = self._requested_fields(
            arguments
        )

        if requested_fields == ("city",):
            if city:
                return (
                    f"{name} si trova a {city}."
                )

            return (
                f"Nel database non è disponibile "
                f"la città di {name}."
            )

        if requested_fields == ("place_type",):
            if place_type:
                return (
                    f"{name} è indicato come "
                    f"{place_type}."
                )

            return (
                f"Nel database non è disponibile "
                f"la tipologia di {name}."
            )

        if requested_fields == ("address",):
            if address:
                return (
                    f"L'indirizzo di {name} "
                    f"è {address}."
                )

            return (
                f"Nel database non è disponibile "
                f"l'indirizzo di {name}."
            )

        if requested_fields == ("coordinates",):
            if (
                latitude is not None
                and longitude is not None
            ):
                return (
                    f"Le coordinate di {name} sono "
                    f"{latitude}, {longitude}."
                )

            return (
                f"Nel database non sono disponibili "
                f"le coordinate di {name}."
            )

        if requested_fields == ("description",):
            if description:
                return description

            return (
                f"Nel database non è disponibile "
                f"una descrizione di {name}."
            )

        facts = []

        if requested_fields == ("overview",):
            selected_fields = {
                "city",
                "place_type",
                "address",
                "coordinates",
                "description",
            }
        else:
            selected_fields = set(
                requested_fields
            )

        if (
            "city" in selected_fields
            and city
        ):
            facts.append(
                f"si trova a {city}"
            )

        if (
            "place_type" in selected_fields
            and place_type
        ):
            facts.append(
                f"è indicato come {place_type}"
            )

        if (
            "address" in selected_fields
            and address
        ):
            facts.append(
                f"l'indirizzo è {address}"
            )

        if (
            "coordinates" in selected_fields
            and latitude is not None
            and longitude is not None
        ):
            facts.append(
                f"le coordinate sono "
                f"{latitude}, {longitude}"
            )

        if (
            "description" in selected_fields
            and description
        ):
            facts.append(
                description.rstrip(".")
            )

        if not facts:
            return (
                f"Nel database è presente {name}, "
                f"ma non risultano i dettagli richiesti."
            )

        return (
            f"{name}: "
            + "; ".join(facts)
            + "."
        )

    @staticmethod
    def _requested_fields(
        arguments: dict[str, Any],
        legacy_key: str | None = None,
    ) -> tuple[str, ...]:
        value = arguments.get(
            "requested_fields"
        )

        if isinstance(value, list):
            fields = tuple(
                item.strip().casefold()
                for item in value
                if isinstance(item, str)
                and item.strip()
            )

            if fields:
                return fields

        if legacy_key is not None:
            legacy_value = arguments.get(
                legacy_key
            )

            if (
                isinstance(legacy_value, str)
                and legacy_value.strip()
            ):
                return (
                    legacy_value
                    .strip()
                    .casefold(),
                )

        return ("overview",)

    @staticmethod
    def _artwork_location_sentence(
        artwork: dict[str, Any],
    ) -> str:
        title = (
            GroundedAnswerRenderer._text(
                artwork.get("title")
            )
            or "Opera senza titolo"
        )
        place_name = GroundedAnswerRenderer._text(
            artwork.get("place_name")
        )
        city = GroundedAnswerRenderer._text(
            artwork.get("city")
        )

        if place_name:
            sentence = (
                f"{title} si trova presso {place_name}"
            )

            #if city:
            #    sentence += f", a {city}"

            return sentence

        if city:
            return (
                f"{title} risulta visitabile a {city}"
            )

        return title

    @staticmethod
    def _data_list(
        result: dict[str, Any],
    ) -> list[dict[str, Any]]:
        data = result.get("data")

        if data is None:
            return []

        if not isinstance(data, list):
            raise TypeError(
                "Il risultato del tool deve contenere "
                "una lista nel campo data"
            )

        if not all(
            isinstance(item, dict)
            for item in data
        ):
            raise TypeError(
                "Gli elementi del risultato devono "
                "essere dizionari"
            )

        return data

    @staticmethod
    def _single_data(
        result: dict[str, Any],
    ) -> dict[str, Any] | None:
        data = result.get("data")

        if data is None:
            return None

        if not isinstance(data, dict):
            raise TypeError(
                "Il risultato del tool deve contenere "
                "un dizionario nel campo data"
            )

        return data

    @staticmethod
    def _text(
        value: Any,
    ) -> str | None:
        if not isinstance(value, str):
            return None

        clean_value = value.strip()

        return clean_value or None
