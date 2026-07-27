import json
from dataclasses import asdict
from pathlib import Path
from typing import Any

from src.core.models import Artist, Artwork, Place
from src.core.normalization import normalize_text


BIRTH_YEAR_PREDICATE = "http://dbpedia.org/ontology/birthYear"
DEATH_YEAR_PREDICATE = "http://dbpedia.org/ontology/deathYear"
TECHNIQUE_PREDICATE = "http://dbpedia.org/ontology/technique"
ADDRESS_PREDICATE = "http://dbpedia.org/ontology/address"
FOAF_NAME_PREDICATE = "http://xmlns.com/foaf/0.1/name"
FOAF_SURNAME_PREDICATE = "http://xmlns.com/foaf/0.1/surname"

NAPLES_URI = "http://it.dbpedia.org/resource/Napoli"
NAPLES_NAME = "Napoli"


def first_literal(
    properties: dict[str, list[dict[str, str | None]]],
    predicate: str,
    language: str | None = None,
) -> str | None:
    for item in properties.get(predicate, []):
        if language is not None and item.get("language") != language:
            continue

        value = item.get("value")

        if value is not None:
            return value

    return None


def build_artist(raw_artist: dict[str, Any]) -> Artist:
    properties = raw_artist["literal_properties"]

    given_name = first_literal(
        properties,
        FOAF_NAME_PREDICATE,
        language="it",
    )
    surname = first_literal(
        properties,
        FOAF_SURNAME_PREDICATE,
        language="it",
    )

    full_name = None

    if given_name and surname:
        full_name = f"{given_name} {surname}"

    birth_place = (
        NAPLES_NAME
        if raw_artist.get("birth_place_uri") == NAPLES_URI
        else None
    )
    death_place = (
        NAPLES_NAME
        if raw_artist.get("death_place_uri") == NAPLES_URI
        else None
    )

    name = raw_artist.get("name")

    if not name:
        raise ValueError("Nome dell'artista mancante")

    return Artist(
        uri=raw_artist["uri"],
        name=name,
        normalized_name=normalize_text(name),
        full_name=full_name,
        birth_date=first_literal(
            properties,
            BIRTH_YEAR_PREDICATE,
        ),
        death_date=first_literal(
            properties,
            DEATH_YEAR_PREDICATE,
        ),
        birth_place=birth_place,
        death_place=death_place,
        description=None,
        image_url=None,
    )


def build_places(
    raw_places: list[dict[str, Any]],
    required_place_uris: set[str],
) -> tuple[list[Place], dict[str, Place]]:
    places: list[Place] = []
    places_by_uri: dict[str, Place] = {}

    for raw_place in raw_places:
        uri = raw_place["uri"]

        if uri not in required_place_uris:
            continue

        name = raw_place.get("name")

        if not name:
            raise ValueError(f"Nome del luogo mancante: {uri}")

        address = first_literal(
            raw_place["literal_properties"],
            ADDRESS_PREDICATE,
            language="it",
        )

        place = Place(
            uri=uri,
            name=name,
            normalized_name=normalize_text(name),
            city=NAPLES_NAME,
            place_type=None,
            address=address,
            latitude=None,
            longitude=None,
            description=None,
            image_url=None,
        )

        places.append(place)
        places_by_uri[uri] = place

    missing_place_uris = required_place_uris - places_by_uri.keys()

    if missing_place_uris:
        missing = ", ".join(sorted(missing_place_uris))
        raise ValueError(f"Luoghi richiesti non trovati: {missing}")

    return places, places_by_uri


def build_artworks(
    raw_artworks: list[dict[str, Any]],
    artist: Artist,
    places_by_uri: dict[str, Place],
) -> list[Artwork]:
    artworks: list[Artwork] = []

    for raw_artwork in raw_artworks:
        if not raw_artwork.get("is_naples_candidate"):
            continue

        title = raw_artwork.get("title")

        if not title:
            raise ValueError(
                f"Titolo dell'opera mancante: {raw_artwork['uri']}"
            )

        venue_uris = raw_artwork.get("venue_uris", [])

        if len(venue_uris) != 1:
            raise ValueError(
                "Ogni opera napoletana deve avere una sola sede: "
                f"{raw_artwork['uri']} → {venue_uris}"
            )

        place = places_by_uri[venue_uris[0]]

        medium = first_literal(
            raw_artwork["literal_properties"],
            TECHNIQUE_PREDICATE,
        )

        artworks.append(
            Artwork(
                uri=raw_artwork["uri"],
                title=title,
                normalized_title=normalize_text(title),
                artist_uri=artist.uri,
                artist_name=artist.name,
                place_uri=place.uri,
                place_name=place.name,
                city=NAPLES_NAME,
                year=None,
                completion_date=None,
                medium=medium,
                subject=None,
                description=None,
                image_url=None,
            )
        )

    return artworks


def build_knowledge(raw_data: dict[str, Any]) -> dict[str, Any]:
    artist = build_artist(raw_data["artist"])

    naples_artworks = [
        artwork
        for artwork in raw_data["artworks"]
        if artwork.get("is_naples_candidate")
    ]

    required_place_uris = {
        venue_uri
        for artwork in naples_artworks
        for venue_uri in artwork.get("venue_uris", [])
    }

    places, places_by_uri = build_places(
        raw_data["places"],
        required_place_uris,
    )

    artworks = build_artworks(
        naples_artworks,
        artist,
        places_by_uri,
    )

    return {
        "metadata": {
            "source": "DBpedia",
            "raw_dataset": "battistello_it_dump.json",
            "city": NAPLES_NAME,
        },
        "artists": [asdict(artist)],
        "places": [asdict(place) for place in places],
        "artworks": [asdict(artwork) for artwork in artworks],
    }


def main() -> None:
    input_path = Path(
        "data/raw/dbpedia/battistello_it_dump.json"
    )
    output_path = Path(
        "data/processed/battistello_knowledge.json"
    )

    with input_path.open(encoding="utf-8") as file:
        raw_data = json.load(file)

    knowledge = build_knowledge(raw_data)

    output_path.parent.mkdir(parents=True, exist_ok=True)

    with output_path.open("w", encoding="utf-8") as file:
        json.dump(
            knowledge,
            file,
            ensure_ascii=False,
            indent=2,
        )
        file.write("\n")

    print(f"Dataset elaborato salvato in: {output_path}")
    print(f"Artisti: {len(knowledge['artists'])}")
    print(f"Luoghi: {len(knowledge['places'])}")
    print(f"Opere: {len(knowledge['artworks'])}")


if __name__ == "__main__":
    main()
