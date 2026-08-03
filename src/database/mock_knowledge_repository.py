import json
from pathlib import Path
from typing import Any

from src.core.interfaces import KnowledgeRepository
from src.core.models import Artist, Artwork, Place
from src.core.normalization import normalize_text


class MockKnowledgeRepository(KnowledgeRepository):
    def __init__(
        self,
        data_path: str | Path | None = None,
    ) -> None:
        if data_path is None:
            data_path = (
                Path(__file__).resolve().parents[2]
                / "data"
                / "processed"
                / "combined_knowledge.json"
            )

        self._data_path = Path(data_path)
        data = self._load_data(self._data_path)

        self._artists = [
            Artist(**self._clean_properties(item))
            for item in data.get("artists", [])
        ]
        self._places = [
            Place(**self._clean_properties(item))
            for item in data.get("places", [])
        ]
        self._artworks = [
            Artwork(**self._clean_properties(item))
            for item in data.get("artworks", [])
        ]

    @staticmethod
    def _load_data(data_path: Path) -> dict[str, Any]:
        with data_path.open(
            "r",
            encoding="utf-8",
        ) as input_file:
            return json.load(input_file)

    @staticmethod
    def _clean_properties(
        properties: dict[str, Any],
    ) -> dict[str, Any]:
        return {
            key: None if value == "" else value
            for key, value in properties.items()
        }

    @staticmethod
    def _validate_limit(limit: int) -> None:
        if limit <= 0:
            raise ValueError(
                "Il limite deve essere maggiore di zero"
            )

    @staticmethod
    def _search_priority(
        normalized_value: str,
        normalized_query: str,
    ) -> int:
        if normalized_value == normalized_query:
            return 0

        if normalized_value.startswith(normalized_query):
            return 1

        return 2

    def check_health(self) -> bool:
        return self._data_path.is_file()

    def get_artwork_by_uri(
        self,
        artwork_uri: str,
    ) -> Artwork | None:
        return next(
            (
                artwork
                for artwork in self._artworks
                if artwork.uri == artwork_uri
            ),
            None,
        )

    def get_artwork_by_title(
        self,
        artwork_title: str,
    ) -> Artwork | None:
        normalized_title = normalize_text(artwork_title)

        if not normalized_title:
            return None

        matches = sorted(
            (
                artwork
                for artwork in self._artworks
                if artwork.normalized_title
                == normalized_title
            ),
            key=lambda artwork: artwork.uri,
        )

        if not matches:
            return None

        return matches[0]

    def search_artworks(
        self,
        query: str,
        limit: int = 5,
    ) -> list[Artwork]:
        self._validate_limit(limit)

        normalized_query = normalize_text(query)

        if not normalized_query:
            return []

        matches = [
            artwork
            for artwork in self._artworks
            if normalized_query
            in artwork.normalized_title
        ]

        matches.sort(
            key=lambda artwork: (
                self._search_priority(
                    artwork.normalized_title,
                    normalized_query,
                ),
                artwork.normalized_title,
                artwork.uri,
            )
        )

        return matches[:limit]

    def list_artworks_by_artist(
        self,
        artist_name: str,
        city: str = "Napoli",
    ) -> list[Artwork]:
        normalized_name = normalize_text(artist_name)

        if not normalized_name:
            return []

        matches = [
            artwork
            for artwork in self._artworks
            if normalize_text(artwork.artist_name)
            == normalized_name
            and artwork.city is not None
            and artwork.city.casefold() == city.casefold()
        ]

        matches.sort(
            key=lambda artwork: (
                artwork.year is None,
                artwork.year or 0,
                artwork.normalized_title,
                artwork.uri,
            )
        )

        return matches

    def list_artworks_by_place(
        self,
        place_name: str,
    ) -> list[Artwork]:
        normalized_name = normalize_text(place_name)

        if not normalized_name:
            return []

        matches = [
            artwork
            for artwork in self._artworks
            if artwork.place_name is not None
            and normalize_text(artwork.place_name)
            == normalized_name
        ]

        matches.sort(
            key=lambda artwork: (
                artwork.year is None,
                artwork.year or 0,
                artwork.normalized_title,
                artwork.uri,
            )
        )

        return matches

    def get_artist_by_name(
        self,
        artist_name: str,
    ) -> Artist | None:
        normalized_name = normalize_text(artist_name)

        if not normalized_name:
            return None

        matches = sorted(
            (
                artist
                for artist in self._artists
                if artist.normalized_name
                == normalized_name
            ),
            key=lambda artist: artist.uri,
        )

        if not matches:
            return None

        return matches[0]

    def get_artist_by_uri(
        self,
        artist_uri: str,
    ) -> Artist | None:
        return next(
            (
                artist
                for artist in self._artists
                if artist.uri == artist_uri
            ),
            None,
        )

    def search_artists(
        self,
        query: str,
        limit: int = 5,
    ) -> list[Artist]:
        self._validate_limit(limit)

        normalized_query = normalize_text(query)

        if not normalized_query:
            return []

        matches = [
            artist
            for artist in self._artists
            if normalized_query
            in artist.normalized_name
        ]

        matches.sort(
            key=lambda artist: (
                self._search_priority(
                    artist.normalized_name,
                    normalized_query,
                ),
                artist.normalized_name,
                artist.uri,
            )
        )

        return matches[:limit]

    def get_place_by_name(
        self,
        place_name: str,
    ) -> Place | None:
        normalized_name = normalize_text(place_name)

        if not normalized_name:
            return None

        matches = sorted(
            (
                place
                for place in self._places
                if place.normalized_name
                == normalized_name
            ),
            key=lambda place: place.uri,
        )

        if not matches:
            return None

        return matches[0]

    def search_places(
        self,
        query: str,
        limit: int = 5,
    ) -> list[Place]:
        self._validate_limit(limit)

        normalized_query = normalize_text(query)

        if not normalized_query:
            return []

        matches = [
            place
            for place in self._places
            if normalized_query
            in place.normalized_name
        ]

        matches.sort(
            key=lambda place: (
                self._search_priority(
                    place.normalized_name,
                    normalized_query,
                ),
                place.normalized_name,
                place.uri,
            )
        )

        return matches[:limit]
