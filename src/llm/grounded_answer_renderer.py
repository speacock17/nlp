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
            "list_artworks_by_place":
                self._render_artworks_by_place,
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
        facts = []

        artist_name = self._text(
            artwork.get("artist_name")
        )
        place_name = self._text(
            artwork.get("place_name")
        )
        city = self._text(
            artwork.get("city")
        )
        year = artwork.get("year")
        completion_date = self._text(
            artwork.get("completion_date")
        )
        medium = self._text(
            artwork.get("medium")
        )
        description = self._text(
            artwork.get("description")
        )

        if artist_name:
            facts.append(
                f"? attribuita a {artist_name}"
            )

        if place_name:
            location = (
                f"si trova presso {place_name}"
            )

            if city:
                location += f", a {city}"

            facts.append(location)

        if year is not None:
            facts.append(
                f"? datata {year}"
            )
        elif completion_date:
            facts.append(
                f"ha data di completamento "
                f"{completion_date}"
            )

        if medium:
            facts.append(
                f"la tecnica indicata ? {medium}"
            )

        if description:
            facts.append(description.rstrip("."))

        if not facts:
            return (
                f"Nel database ? presente {title}, "
                f"ma non risultano altri dettagli."
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
        facts = []

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

        if full_name and full_name != name:
            facts.append(
                f"il nome completo ? {full_name}"
            )

        if birth_date:
            birth_fact = f"nacque il {birth_date}"

            if birth_place:
                birth_fact += f" a {birth_place}"

            facts.append(birth_fact)
        elif birth_place:
            facts.append(
                f"nacque a {birth_place}"
            )

        if death_date:
            death_fact = f"mor? il {death_date}"

            if death_place:
                death_fact += f" a {death_place}"

            facts.append(death_fact)
        elif death_place:
            facts.append(
                f"mor? a {death_place}"
            )

        if description:
            facts.append(description.rstrip("."))

        if not facts:
            return (
                f"Nel database ? presente {name}, "
                f"ma non risultano altri dettagli."
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
        facts = []

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

        if place_type:
            facts.append(
                f"? indicato come {place_type}"
            )

        if city:
            facts.append(
                f"si trova a {city}"
            )

        if address:
            facts.append(
                f"l'indirizzo ? {address}"
            )

        if description:
            facts.append(description.rstrip("."))

        if not facts:
            return (
                f"Nel database ? presente {name}, "
                f"ma non risultano altri dettagli."
            )

        return (
            f"{name}: "
            + "; ".join(facts)
            + "."
        )

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

            if city:
                sentence += f", a {city}"

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
