import json
import os
from pathlib import Path
from typing import Any

from dotenv import load_dotenv
from neo4j import Driver, GraphDatabase, ManagedTransaction

from src.core.models import Artist, Artwork, Place


DEFAULT_DATASET_PATH = Path(
    "data/processed/combined_knowledge.json"
)


def load_dataset(path: Path) -> dict[str, Any]:
    if not path.is_file():
        raise FileNotFoundError(f"Dataset non trovato: {path}")

    with path.open(encoding="utf-8") as file:
        data = json.load(file)

    for collection_name in ("artists", "places", "artworks"):
        collection = data.get(collection_name)

        if not isinstance(collection, list):
            raise ValueError(
                f"Collezione non valida: {collection_name}"
            )

    artists = [
        Artist(**item)
        for item in data["artists"]
    ]
    places = [
        Place(**item)
        for item in data["places"]
    ]
    artworks = [
        Artwork(**item)
        for item in data["artworks"]
    ]

    artist_uris = {artist.uri for artist in artists}
    place_uris = {place.uri for place in places}

    for artwork in artworks:
        if artwork.artist_uri not in artist_uris:
            raise ValueError(
                f"Artista inesistente per l'opera {artwork.uri}"
            )

        if (
            artwork.place_uri is not None
            and artwork.place_uri not in place_uris
        ):
            raise ValueError(
                f"Luogo inesistente per l'opera {artwork.uri}"
            )

    return data


def without_none(properties: dict[str, Any]) -> dict[str, Any]:
    return {
        key: value
        for key, value in properties.items()
        if value is not None
    }


def prepare_rows(
    items: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    return [
        without_none(item)
        for item in items
    ]


def write_knowledge(
    transaction: ManagedTransaction,
    dataset: dict[str, Any],
) -> None:
    artists = prepare_rows(dataset["artists"])
    places = prepare_rows(dataset["places"])
    artworks = prepare_rows(dataset["artworks"])

    transaction.run(
        """
        UNWIND $artists AS properties
        MERGE (artist:Artist {uri: properties.uri})
        SET artist = properties
        """,
        artists=artists,
    ).consume()

    transaction.run(
        """
        UNWIND $places AS properties
        MERGE (place:Place {uri: properties.uri})
        SET place = properties
        """,
        places=places,
    ).consume()

    transaction.run(
        """
        UNWIND $artworks AS properties
        MERGE (artwork:Artwork {uri: properties.uri})
        SET artwork = properties
        """,
        artworks=artworks,
    ).consume()

    transaction.run(
        """
        UNWIND $artworks AS properties
        MATCH (artwork:Artwork {uri: properties.uri})
        OPTIONAL MATCH (:Artist)-[created:CREATED]->(artwork)
        DELETE created
        WITH artwork, properties
        MATCH (artist:Artist {uri: properties.artist_uri})
        MERGE (artist)-[:CREATED]->(artwork)
        """,
        artworks=artworks,
    ).consume()

    transaction.run(
        """
        UNWIND $artworks AS properties
        MATCH (artwork:Artwork {uri: properties.uri})
        OPTIONAL MATCH (artwork)-[displayed:DISPLAYED_AT]->(:Place)
        DELETE displayed
        WITH artwork, properties
        WHERE properties.place_uri IS NOT NULL
        MATCH (place:Place {uri: properties.place_uri})
        MERGE (artwork)-[:DISPLAYED_AT]->(place)
        """,
        artworks=artworks,
    ).consume()


def count_graph(driver: Driver, database: str) -> dict[str, int]:
    records, _, _ = driver.execute_query(
        """
        MATCH (artist:Artist)
        WITH count(artist) AS artists
        MATCH (artwork:Artwork)
        WITH artists, count(artwork) AS artworks
        MATCH (place:Place)
        WITH artists, artworks, count(place) AS places
        MATCH (:Artist)-[created:CREATED]->(:Artwork)
        WITH
            artists,
            artworks,
            places,
            count(created) AS created_relationships
        MATCH (:Artwork)-[displayed:DISPLAYED_AT]->(:Place)
        RETURN
            artists,
            artworks,
            places,
            created_relationships,
            count(displayed) AS displayed_relationships
        """,
        database_=database,
    )

    if len(records) != 1:
        raise RuntimeError(
            "Impossibile ottenere i conteggi del grafo"
        )

    return dict(records[0])


def create_driver() -> tuple[Driver, str]:
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

    driver = GraphDatabase.driver(
        uri,
        auth=(user, password),
    )

    return driver, database


def main() -> None:
    dataset = load_dataset(DEFAULT_DATASET_PATH)
    driver, database = create_driver()

    try:
        driver.verify_connectivity()

        with driver.session(database=database) as session:
            session.execute_write(
                write_knowledge,
                dataset,
            )

        counts = count_graph(driver, database)
    finally:
        driver.close()

    print(
        "Dataset caricato: "
        f"{DEFAULT_DATASET_PATH}"
    )
    print(f"Artisti: {counts['artists']}")
    print(f"Opere: {counts['artworks']}")
    print(f"Luoghi: {counts['places']}")
    print(
        "Relazioni CREATED: "
        f"{counts['created_relationships']}"
    )
    print(
        "Relazioni DISPLAYED_AT: "
        f"{counts['displayed_relationships']}"
    )


if __name__ == "__main__":
    main()
