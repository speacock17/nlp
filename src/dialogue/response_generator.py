from src.core.enums import EntityType, Intent
from src.core.interfaces import KnowledgeRepository
from src.core.models import (
    Artist,
    Artwork,
    BotResponse,
    Inconsistency,
    NLUResult,
    Place,
)


class ResponseGenerator:
    def __init__(
        self,
        knowledge_repository: KnowledgeRepository,
    ) -> None:
        self._knowledge_repository = knowledge_repository

    def generate(
        self,
        nlu_result: NLUResult,
        inconsistency: Inconsistency | None = None,
    ) -> BotResponse:
        if inconsistency is not None:
            return BotResponse(
                text=inconsistency.message,
                intent=nlu_result.intent,
                inconsistency=inconsistency,
            )

        handlers = {
            Intent.LIST_ARTWORKS_BY_ARTIST:
                self._list_artworks_by_artist,
            Intent.ARTWORK_LOCATION:
                self._artwork_location,
            Intent.ARTWORK_AUTHOR:
                self._artwork_author,
            Intent.ARTWORK_DATE:
                self._artwork_date,
            Intent.ARTWORK_DESCRIPTION:
                self._artwork_description,
            Intent.ARTIST_INFO:
                self._artist_info,
            Intent.LIST_PLACES:
                self._list_places,
            Intent.PLACE_ARTWORKS:
                self._place_artworks,
            Intent.COMPARE_ARTISTS:
                self._compare_artists,
            Intent.OUT_OF_SCOPE:
                self._out_of_scope,
            Intent.UNKNOWN:
                self._unknown,
        }

        handler = handlers.get(nlu_result.intent)

        if handler is None:
            return self._unknown(nlu_result)

        return handler(nlu_result)

    @staticmethod
    def _first_entity_uri(
        nlu_result: NLUResult,
        entity_type: EntityType,
    ) -> str | None:
        entity = next(
            (
                item
                for item in nlu_result.entities
                if item.entity_type == entity_type
            ),
            None,
        )

        if entity is None:
            return None

        return entity.uri

    @staticmethod
    def _first_entity_name(
        nlu_result: NLUResult,
        entity_type: EntityType,
    ) -> str | None:
        entity = next(
            (
                item
                for item in nlu_result.entities
                if item.entity_type == entity_type
            ),
            None,
        )

        if entity is None:
            return None

        return entity.canonical_name

    def _get_artwork(
        self,
        nlu_result: NLUResult,
    ) -> Artwork | None:
        artwork_uri = self._first_entity_uri(
            nlu_result,
            EntityType.ARTWORK,
        )

        if artwork_uri is None:
            return None

        return self._knowledge_repository.get_artwork_by_uri(
            artwork_uri
        )

    def _get_artist(
        self,
        nlu_result: NLUResult,
    ) -> Artist | None:
        artist_uri = self._first_entity_uri(
            nlu_result,
            EntityType.ARTIST,
        )

        if artist_uri is None:
            return None

        return self._knowledge_repository.get_artist_by_uri(
            artist_uri
        )

    def _get_place(
        self,
        nlu_result: NLUResult,
    ) -> Place | None:
        place_name = self._first_entity_name(
            nlu_result,
            EntityType.PLACE,
        )

        if place_name is None:
            return None

        return self._knowledge_repository.get_place_by_name(
            place_name
        )

    def _list_artworks_by_artist(
        self,
        nlu_result: NLUResult,
    ) -> BotResponse:
        artist = self._get_artist(nlu_result)

        if artist is None:
            return self._clarification_response(
                nlu_result.intent,
                "Quale artista intendi?",
            )

        artworks = (
            self._knowledge_repository
            .list_artworks_by_artist(artist.name)
        )

        if not artworks:
            return BotResponse(
                text=(
                    f"Non risultano opere di {artist.name} "
                    "visitabili a Napoli."
                ),
                intent=nlu_result.intent,
                artists=[artist],
            )

        titles = ", ".join(
            artwork.title
            for artwork in artworks
        )

        return BotResponse(
            text=(
                f"Le opere di {artist.name} visitabili "
                f"a Napoli sono: {titles}."
            ),
            intent=nlu_result.intent,
            artworks=artworks,
            artists=[artist],
        )

    def _artwork_location(
        self,
        nlu_result: NLUResult,
    ) -> BotResponse:
        artwork = self._get_artwork(nlu_result)

        if artwork is None:
            return self._clarification_response(
                nlu_result.intent,
                "Di quale opera vuoi conoscere il luogo?",
            )

        if artwork.place_name is None:
            text = (
                f"Non ho informazioni sul luogo in cui "
                f"si trova {artwork.title}."
            )
        else:
            text = (
                f"{artwork.title} si trova presso "
                f"{artwork.place_name}."
            )

        return BotResponse(
            text=text,
            intent=nlu_result.intent,
            artworks=[artwork],
        )

    def _artwork_author(
        self,
        nlu_result: NLUResult,
    ) -> BotResponse:
        artwork = self._get_artwork(nlu_result)

        if artwork is None:
            return self._clarification_response(
                nlu_result.intent,
                "Di quale opera vuoi conoscere l'autore?",
            )

        return BotResponse(
            text=(
                f"{artwork.title} è stata realizzata da "
                f"{artwork.artist_name}."
            ),
            intent=nlu_result.intent,
            artworks=[artwork],
        )

    def _artwork_date(
        self,
        nlu_result: NLUResult,
    ) -> BotResponse:
        artwork = self._get_artwork(nlu_result)

        if artwork is None:
            return self._clarification_response(
                nlu_result.intent,
                "Di quale opera vuoi conoscere la data?",
            )

        if artwork.year is None:
            text = (
                f"Non ho una data disponibile per "
                f"{artwork.title}."
            )
        else:
            text = (
                f"{artwork.title} risale al "
                f"{artwork.year}."
            )

        return BotResponse(
            text=text,
            intent=nlu_result.intent,
            artworks=[artwork],
        )

    def _artwork_description(
        self,
        nlu_result: NLUResult,
    ) -> BotResponse:
        artwork = self._get_artwork(nlu_result)

        if artwork is None:
            return self._clarification_response(
                nlu_result.intent,
                "Quale opera vuoi che descriva?",
            )

        description = artwork.description

        if description is None:
            description = (
                f"{artwork.title} è un'opera di "
                f"{artwork.artist_name}."
            )

        return BotResponse(
            text=description,
            intent=nlu_result.intent,
            artworks=[artwork],
        )

    def _artist_info(
        self,
        nlu_result: NLUResult,
    ) -> BotResponse:
        artist = self._get_artist(nlu_result)

        if artist is None:
            return self._clarification_response(
                nlu_result.intent,
                "Di quale artista vuoi informazioni?",
            )

        details = [
            artist.description,
            (
                f"Nacque il {artist.birth_date}."
                if artist.birth_date is not None
                else None
            ),
            (
                f"Morì il {artist.death_date}."
                if artist.death_date is not None
                else None
            ),
        ]

        text = " ".join(
            detail
            for detail in details
            if detail is not None
        )

        if not text:
            text = (
                f"Non ho ulteriori informazioni su "
                f"{artist.name}."
            )

        return BotResponse(
            text=text,
            intent=nlu_result.intent,
            artists=[artist],
        )

    def _list_places(
        self,
        nlu_result: NLUResult,
    ) -> BotResponse:
        places = self._knowledge_repository.list_places()

        if not places:
            text = (
                "Non risultano luoghi visitabili "
                "nel database."
            )
        else:
            names = ", ".join(
                place.name
                for place in places
            )
            text = (
                "Le opere presenti nel database sono "
                f"visitabili presso: {names}."
            )

        return BotResponse(
            text=text,
            intent=nlu_result.intent,
            places=places,
        )

    def _place_artworks(
        self,
        nlu_result: NLUResult,
    ) -> BotResponse:
        place = self._get_place(nlu_result)

        if place is None:
            return self._clarification_response(
                nlu_result.intent,
                "Quale luogo intendi?",
            )

        artworks = (
            self._knowledge_repository
            .list_artworks_by_place(place.name)
        )

        if not artworks:
            text = (
                f"Non risultano opere presenti presso "
                f"{place.name}."
            )
        else:
            titles = ", ".join(
                artwork.title
                for artwork in artworks
            )
            text = (
                f"Presso {place.name} puoi vedere: "
                f"{titles}."
            )

        return BotResponse(
            text=text,
            intent=nlu_result.intent,
            artworks=artworks,
            places=[place],
        )

    def _compare_artists(
        self,
        nlu_result: NLUResult,
    ) -> BotResponse:
        artists = []

        for entity in nlu_result.entities:
            if (
                entity.entity_type == EntityType.ARTIST
                and entity.uri is not None
            ):
                artist = (
                    self._knowledge_repository
                    .get_artist_by_uri(entity.uri)
                )

                if (
                    artist is not None
                    and artist not in artists
                ):
                    artists.append(artist)

        if len(artists) < 2:
            return self._clarification_response(
                nlu_result.intent,
                "Quali due artisti vuoi confrontare?",
            )

        first, second = artists[:2]

        first_artworks = (
            self._knowledge_repository
            .list_artworks_by_artist(first.name)
        )
        second_artworks = (
            self._knowledge_repository
            .list_artworks_by_artist(second.name)
        )

        return BotResponse(
            text=(
                f"{first.name} ha "
                f"{len(first_artworks)} opere visitabili "
                f"a Napoli, mentre {second.name} ne ha "
                f"{len(second_artworks)}."
            ),
            intent=nlu_result.intent,
            artworks=first_artworks + second_artworks,
            artists=[first, second],
        )

    @staticmethod
    def _out_of_scope(
        nlu_result: NLUResult,
    ) -> BotResponse:
        return BotResponse(
            text=(
                "Posso rispondere a domande sulle opere "
                "di Caravaggio e Battistello Caracciolo "
                "visitabili a Napoli."
            ),
            intent=nlu_result.intent,
        )

    @staticmethod
    def _unknown(
        nlu_result: NLUResult,
    ) -> BotResponse:
        return BotResponse(
            text=(
                "Non ho capito la domanda. Puoi "
                "riformularla indicando un artista, "
                "un'opera o un luogo?"
            ),
            intent=nlu_result.intent,
            needs_clarification=True,
        )

    @staticmethod
    def _clarification_response(
        intent: Intent,
        message: str,
    ) -> BotResponse:
        return BotResponse(
            text=message,
            intent=intent,
            needs_clarification=True,
        )
