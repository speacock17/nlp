import os
from typing import Any

from dotenv import load_dotenv
from neo4j import Driver, GraphDatabase
from neo4j.exceptions import Neo4jError

from src.core.interfaces import KnowledgeRepository
from src.core.models import Artist, Artwork, Place
from src.core.normalization import normalize_text


class Neo4jKnowledgeRepository(KnowledgeRepository):
    def __init__(
        self,
        uri: str,
        user: str,
        password: str,
        database: str = "neo4j",
    ) -> None:
        self._driver = GraphDatabase.driver(
            uri,
            auth=(user, password),
        )
        self._database = database

    @classmethod
    def from_env(cls) -> "Neo4jKnowledgeRepository":
        load_dotenv()

        uri = os.getenv("NEO4J_URI")
        user = os.getenv("NEO4J_USER")
        password = os.getenv("NEO4J_PASSWORD")
        database = os.getenv("NEO4J_DATABASE", "neo4j")

        missing = [
            name
            for name, value in (
                ("NEO4J_URI", uri),
                ("NEO4J_USER", user),
                ("NEO4J_PASSWORD", password),
            )
            if not value
        ]

        if missing:
            raise RuntimeError(
                "Variabili d'ambiente mancanti: "
                + ", ".join(missing)
            )

        return cls(
            uri=uri,
            user=user,
            password=password,
            database=database,
        )

    def close(self) -> None:
        self._driver.close()

    def __enter__(self) -> "Neo4jKnowledgeRepository":
        return self

    def __exit__(
        self,
        exception_type: type[BaseException] | None,
        exception: BaseException | None,
        traceback: Any,
    ) -> None:
        self.close()

    def check_health(self) -> bool:
        try:
            records, _, _ = self._driver.execute_query(
                "RETURN 1 AS value",
                database_=self._database,
            )
        except Neo4jError:
            return False

        return (
            len(records) == 1
            and records[0]["value"] == 1
        )

    @staticmethod
    def _validate_limit(limit: int) -> None:
        if limit <= 0:
            raise ValueError(
                "Il limite deve essere maggiore di zero"
            )

    @staticmethod
    def _to_artist(properties: dict[str, Any]) -> Artist:
        return Artist(**properties)

    @staticmethod
    def _to_artwork(properties: dict[str, Any]) -> Artwork:
        return Artwork(**properties)

    @staticmethod
    def _to_place(properties: dict[str, Any]) -> Place:
        return Place(**properties)

    def _get_single_node(
        self,
        query: str,
        node_key: str,
        parameters: dict[str, Any],
    ) -> dict[str, Any] | None:
        records, _, _ = self._driver.execute_query(
            query,
            parameters_=parameters,
            database_=self._database,
        )

        if not records:
            return None

        return dict(records[0][node_key])

    def _get_many_nodes(
        self,
        query: str,
        node_key: str,
        parameters: dict[str, Any],
    ) -> list[dict[str, Any]]:
        records, _, _ = self._driver.execute_query(
            query,
            parameters_=parameters,
            database_=self._database,
        )

        return [
            dict(record[node_key])
            for record in records
        ]

    def get_artwork_by_uri(
        self,
        artwork_uri: str,
    ) -> Artwork | None:
        properties = self._get_single_node(
            """
            MATCH (artwork:Artwork {uri: $uri})
            RETURN artwork
            LIMIT 1
            """,
            "artwork",
            {"uri": artwork_uri},
        )

        if properties is None:
            return None

        return self._to_artwork(properties)

    def get_artwork_by_title(
        self,
        artwork_title: str,
    ) -> Artwork | None:
        normalized_title = normalize_text(artwork_title)

        if not normalized_title:
            return None

        properties = self._get_single_node(
            """
            MATCH (artwork:Artwork {
                normalized_title: $normalized_title
            })
            RETURN artwork
            ORDER BY artwork.uri
            LIMIT 1
            """,
            "artwork",
            {"normalized_title": normalized_title},
        )

        if properties is None:
            return None

        return self._to_artwork(properties)

    def search_artworks(
        self,
        query: str,
        limit: int = 5,
    ) -> list[Artwork]:
        self._validate_limit(limit)

        normalized_query = normalize_text(query)

        if not normalized_query:
            return []

        properties = self._get_many_nodes(
            """
            MATCH (artwork:Artwork)
            WHERE artwork.normalized_title
                CONTAINS $normalized_query
            RETURN artwork
            ORDER BY
                CASE
                    WHEN artwork.normalized_title =
                        $normalized_query
                    THEN 0
                    WHEN artwork.normalized_title
                        STARTS WITH $normalized_query
                    THEN 1
                    ELSE 2
                END,
                artwork.normalized_title,
                artwork.uri
            LIMIT $limit
            """,
            "artwork",
            {
                "normalized_query": normalized_query,
                "limit": limit,
            },
        )

        return [
            self._to_artwork(item)
            for item in properties
        ]

    def list_artworks_by_artist(
        self,
        artist_name: str,
        city: str = "Napoli",
    ) -> list[Artwork]:
        normalized_name = normalize_text(artist_name)

        if not normalized_name:
            return []

        properties = self._get_many_nodes(
            """
            MATCH (artist:Artist {
                normalized_name: $normalized_name
            })-[:CREATED]->(artwork:Artwork)
            WHERE
                artwork.city IS NOT NULL
                AND toLower(artwork.city) = toLower($city)
            RETURN artwork
            ORDER BY
                artwork.year,
                artwork.normalized_title,
                artwork.uri
            """,
            "artwork",
            {
                "normalized_name": normalized_name,
                "city": city,
            },
        )

        return [
            self._to_artwork(item)
            for item in properties
        ]

    def list_artworks_by_place(
        self,
        place_name: str,
    ) -> list[Artwork]:
        normalized_name = normalize_text(place_name)

        if not normalized_name:
            return []

        properties = self._get_many_nodes(
            """
            MATCH (artwork:Artwork)-[:DISPLAYED_AT]->
                  (place:Place {
                      normalized_name: $normalized_name
                  })
            RETURN artwork
            ORDER BY
                artwork.year,
                artwork.normalized_title,
                artwork.uri
            """,
            "artwork",
            {"normalized_name": normalized_name},
        )

        return [
            self._to_artwork(item)
            for item in properties
        ]

    def get_artist_by_name(
        self,
        artist_name: str,
    ) -> Artist | None:
        normalized_name = normalize_text(artist_name)

        if not normalized_name:
            return None

        properties = self._get_single_node(
            """
            MATCH (artist:Artist {
                normalized_name: $normalized_name
            })
            RETURN artist
            ORDER BY artist.uri
            LIMIT 1
            """,
            "artist",
            {"normalized_name": normalized_name},
        )

        if properties is None:
            return None

        return self._to_artist(properties)

    def get_artist_by_uri(
        self,
        artist_uri: str,
    ) -> Artist | None:
        properties = self._get_single_node(
            """
            MATCH (artist:Artist {uri: $uri})
            RETURN artist
            LIMIT 1
            """,
            "artist",
            {"uri": artist_uri},
        )

        if properties is None:
            return None

        return self._to_artist(properties)

    def search_artists(
        self,
        query: str,
        limit: int = 5,
    ) -> list[Artist]:
        self._validate_limit(limit)

        normalized_query = normalize_text(query)

        if not normalized_query:
            return []

        properties = self._get_many_nodes(
            """
            MATCH (artist:Artist)
            WHERE artist.normalized_name
                CONTAINS $normalized_query
            RETURN artist
            ORDER BY
                CASE
                    WHEN artist.normalized_name =
                        $normalized_query
                    THEN 0
                    WHEN artist.normalized_name
                        STARTS WITH $normalized_query
                    THEN 1
                    ELSE 2
                END,
                artist.normalized_name,
                artist.uri
            LIMIT $limit
            """,
            "artist",
            {
                "normalized_query": normalized_query,
                "limit": limit,
            },
        )

        return [
            self._to_artist(item)
            for item in properties
        ]

    def get_place_by_name(
        self,
        place_name: str,
    ) -> Place | None:
        normalized_name = normalize_text(place_name)

        if not normalized_name:
            return None

        properties = self._get_single_node(
            """
            MATCH (place:Place {
                normalized_name: $normalized_name
            })
            RETURN place
            ORDER BY place.uri
            LIMIT 1
            """,
            "place",
            {"normalized_name": normalized_name},
        )

        if properties is None:
            return None

        return self._to_place(properties)

    def search_places(
        self,
        query: str,
        limit: int = 5,
    ) -> list[Place]:
        self._validate_limit(limit)

        normalized_query = normalize_text(query)

        if not normalized_query:
            return []

        properties = self._get_many_nodes(
            """
            MATCH (place:Place)
            WHERE place.normalized_name
                CONTAINS $normalized_query
            RETURN place
            ORDER BY
                CASE
                    WHEN place.normalized_name =
                        $normalized_query
                    THEN 0
                    WHEN place.normalized_name
                        STARTS WITH $normalized_query
                    THEN 1
                    ELSE 2
                END,
                place.normalized_name,
                place.uri
            LIMIT $limit
            """,
            "place",
            {
                "normalized_query": normalized_query,
                "limit": limit,
            },
        )

        return [
            self._to_place(item)
            for item in properties
        ]
