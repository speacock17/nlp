import json
from dataclasses import asdict
from pathlib import Path
from typing import Any

from src.core.models import Artist, Artwork, Place
from src.core.normalization import normalize_text


CITY = "Napoli"


def binding_value(
    row: dict[str, Any],
    field: str,
) -> str | None:
    binding = row.get(field)

    if not binding:
        return None

    value = binding.get("value")

    if value is None:
        return None

    return str(value)


def required_binding(
    row: dict[str, Any],
    field: str,
) -> str:
    value = binding_value(row, field)

    if value is None or not value.strip():
        raise ValueError(f"Campo obbligatorio mancante: {field}")

    return value


def optional_float(
    row: dict[str, Any],
    field: str,
) -> float | None:
    value = binding_value(row, field)

    if value is None:
        return None

    try:
        return float(value)
    except ValueError as error:
        raise ValueError(
            f"Valore non convertibile in float per {field}: {value}"
        ) from error


def optional_int(
    row: dict[str, Any],
    field: str,
) -> int | None:
    value = binding_value(row, field)

    if value is None:
        return None

    try:
        return int(value)
    except ValueError as error:
        raise ValueError(
            f"Valore non convertibile in int per {field}: {value}"
        ) from error


def load_bindings(path: Path) -> list[dict[str, Any]]:
    if not path.is_file():
        raise FileNotFoundError(f"File JSON non trovato: {path}")

    with path.open(encoding="utf-8") as file:
        data = json.load(file)

    try:
        bindings = data["results"]["bindings"]
    except (KeyError, TypeError) as error:
        raise ValueError(
            f"Struttura SPARQL JSON non valida: {path}"
        ) from error

    if not isinstance(bindings, list):
        raise ValueError(
            f"Il campo bindings non è una lista: {path}"
        )

    return bindings


def build_artist(
    artist_bindings: list[dict[str, Any]],
) -> Artist:
    if len(artist_bindings) != 1:
        raise ValueError(
            "La query dell'artista deve restituire una sola riga"
        )

    row = artist_bindings[0]

    uri = required_binding(row, "artist")
    name = required_binding(row, "name")

    return Artist(
        uri=uri,
        name=name,
        normalized_name=normalize_text(name),
        full_name=binding_value(row, "fullName"),
        birth_date=binding_value(row, "birthDate"),
        death_date=binding_value(row, "deathDate"),
        birth_place=binding_value(row, "birthPlace"),
        death_place=binding_value(row, "deathPlace"),
        description=binding_value(row, "description"),
        image_url=binding_value(row, "image"),
    )


def build_places(
    place_bindings: list[dict[str, Any]],
) -> tuple[list[Place], dict[str, Place]]:
    places: list[Place] = []
    places_by_uri: dict[str, Place] = {}

    for row in place_bindings:
        uri = required_binding(row, "place")
        name = required_binding(row, "name")

        if uri in places_by_uri:
            raise ValueError(f"Luogo duplicato: {uri}")

        place = Place(
            uri=uri,
            name=name,
            normalized_name=normalize_text(name),
            city=CITY,
            place_type=None,
            address=binding_value(row, "address"),
            latitude=optional_float(row, "latitude"),
            longitude=optional_float(row, "longitude"),
            description=binding_value(row, "description"),
            image_url=binding_value(row, "image"),
        )

        places.append(place)
        places_by_uri[uri] = place

    return places, places_by_uri


def build_artworks(
    artwork_bindings: list[dict[str, Any]],
    artist: Artist,
    places_by_uri: dict[str, Place],
) -> list[Artwork]:
    artworks: list[Artwork] = []
    artwork_uris: set[str] = set()

    for row in artwork_bindings:
        uri = required_binding(row, "artwork")
        title = required_binding(row, "title")
        artist_uri = required_binding(row, "artist")
        artist_name = required_binding(row, "artistName")
        place_uri = required_binding(row, "place")

        if uri in artwork_uris:
            raise ValueError(f"Opera duplicata: {uri}")

        if artist_uri != artist.uri:
            raise ValueError(
                f"Artista non coerente per l'opera {uri}"
            )

        if artist_name != artist.name:
            raise ValueError(
                f"Nome artista non coerente per l'opera {uri}"
            )

        place = places_by_uri.get(place_uri)

        if place is None:
            raise ValueError(
                f"Luogo dell'opera non trovato: {place_uri}"
            )

        artworks.append(
            Artwork(
                uri=uri,
                title=title,
                normalized_title=normalize_text(title),
                artist_uri=artist.uri,
                artist_name=artist.name,
                place_uri=place.uri,
                place_name=place.name,
                city=CITY,
                year=optional_int(row, "year"),
                completion_date=binding_value(
                    row,
                    "completionDate",
                ),
                medium=binding_value(row, "medium"),
                subject=None,
                description=binding_value(
                    row,
                    "description",
                ),
                image_url=binding_value(row, "image"),
            )
        )

        artwork_uris.add(uri)

    return artworks


def build_knowledge() -> dict[str, Any]:
    raw_directory = Path("data/raw/dbpedia")

    artist_bindings = load_bindings(
        raw_directory / "caravaggio_artist_details.json"
    )
    place_bindings = load_bindings(
        raw_directory / "caravaggio_places_details.json"
    )
    artwork_bindings = load_bindings(
        raw_directory / "caravaggio_artworks_details.json"
    )

    artist = build_artist(artist_bindings)
    places, places_by_uri = build_places(place_bindings)
    artworks = build_artworks(
        artwork_bindings,
        artist,
        places_by_uri,
    )

    return {
        "metadata": {
            "source": "DBpedia",
            "city": CITY,
            "raw_datasets": [
                "caravaggio_artist_details.json",
                "caravaggio_places_details.json",
                "caravaggio_artworks_details.json",
            ],
        },
        "artists": [asdict(artist)],
        "places": [
            asdict(place)
            for place in sorted(
                places,
                key=lambda item: item.uri,
            )
        ],
        "artworks": [
            asdict(artwork)
            for artwork in sorted(
                artworks,
                key=lambda item: item.uri,
            )
        ],
    }


def main() -> None:
    output_path = Path(
        "data/processed/caravaggio_knowledge.json"
    )

    knowledge = build_knowledge()

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
