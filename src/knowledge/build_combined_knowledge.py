import json
from pathlib import Path
from typing import Any

from src.core.models import Artist, Artwork, Place
from src.core.normalization import normalize_text


PLACE_URI_ALIASES = {
    (
        "http://it.dbpedia.org/resource/"
        "Museo_nazionale_di_Capodimonte"
    ): "http://dbpedia.org/resource/Museo_di_Capodimonte",
    (
        "http://it.dbpedia.org/resource/"
        "Pio_Monte_della_Misericordia"
    ): "http://dbpedia.org/resource/Pio_Monte_della_Misericordia",
}

INPUT_PATHS = (
    Path("data/processed/caravaggio_knowledge.json"),
    Path("data/processed/battistello_knowledge.json"),
)

OUTPUT_PATH = Path("data/processed/combined_knowledge.json")


def load_json(path: Path) -> dict[str, Any]:
    if not path.is_file():
        raise FileNotFoundError(f"Dataset non trovato: {path}")

    with path.open(encoding="utf-8") as file:
        data = json.load(file)

    for collection_name in ("artists", "places", "artworks"):
        if not isinstance(data.get(collection_name), list):
            raise ValueError(
                f"Collezione non valida in {path}: {collection_name}"
            )

    return data


def canonical_place_uri(uri: str) -> str:
    return PLACE_URI_ALIASES.get(uri, uri)


def merge_place(
    existing: dict[str, Any],
    incoming: dict[str, Any],
) -> dict[str, Any]:
    result = existing.copy()

    required_fields = (
        "name",
        "normalized_name",
        "city",
    )

    for field in required_fields:
        existing_value = result.get(field)
        incoming_value = incoming.get(field)

        if (
            existing_value is not None
            and incoming_value is not None
            and existing_value != incoming_value
        ):
            raise ValueError(
                f"Conflitto sul campo {field} per il luogo "
                f"{result['uri']}: "
                f"{existing_value!r} != {incoming_value!r}"
            )

    for field, incoming_value in incoming.items():
        if field == "uri":
            continue

        existing_value = result.get(field)

        if existing_value is None and incoming_value is not None:
            result[field] = incoming_value

    return result


def merge_datasets(
    datasets: list[dict[str, Any]],
) -> dict[str, Any]:
    artists_by_uri: dict[str, dict[str, Any]] = {}
    places_by_uri: dict[str, dict[str, Any]] = {}
    artworks_by_uri: dict[str, dict[str, Any]] = {}

    for dataset in datasets:
        for artist in dataset["artists"]:
            uri = artist["uri"]

            if uri in artists_by_uri:
                raise ValueError(f"Artista duplicato: {uri}")

            artists_by_uri[uri] = artist.copy()

        for place in dataset["places"]:
            canonical_uri = canonical_place_uri(place["uri"])

            canonical_place = place.copy()
            canonical_place["uri"] = canonical_uri

            existing = places_by_uri.get(canonical_uri)

            if existing is None:
                places_by_uri[canonical_uri] = canonical_place
            else:
                places_by_uri[canonical_uri] = merge_place(
                    existing,
                    canonical_place,
                )

        for artwork in dataset["artworks"]:
            uri = artwork["uri"]

            if uri in artworks_by_uri:
                raise ValueError(f"Opera duplicata: {uri}")

            canonical_artwork = artwork.copy()

            place_uri = canonical_artwork.get("place_uri")

            if place_uri is not None:
                canonical_artwork["place_uri"] = canonical_place_uri(
                    place_uri
                )

            artworks_by_uri[uri] = canonical_artwork

    for artwork in artworks_by_uri.values():
        place_uri = artwork.get("place_uri")

        if place_uri is None:
            continue

        place = places_by_uri.get(place_uri)

        if place is None:
            raise ValueError(
                f"Luogo non trovato per l'opera "
                f"{artwork['uri']}: {place_uri}"
            )

        artwork["place_name"] = place["name"]

    return {
        "metadata": {
            "source": "DBpedia",
            "city": "Napoli",
            "input_datasets": [
                path.name
                for path in INPUT_PATHS
            ],
            "place_uri_aliases": PLACE_URI_ALIASES,
        },
        "artists": [
            artists_by_uri[uri]
            for uri in sorted(artists_by_uri)
        ],
        "places": [
            places_by_uri[uri]
            for uri in sorted(places_by_uri)
        ],
        "artworks": [
            artworks_by_uri[uri]
            for uri in sorted(artworks_by_uri)
        ],
    }


def validate_knowledge(data: dict[str, Any]) -> None:
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
    artwork_uris = {artwork.uri for artwork in artworks}

    if len(artist_uris) != len(artists):
        raise ValueError("Sono presenti URI artista duplicate")

    if len(place_uris) != len(places):
        raise ValueError("Sono presenti URI luogo duplicate")

    if len(artwork_uris) != len(artworks):
        raise ValueError("Sono presenti URI opera duplicate")

    for artist in artists:
        if artist.normalized_name != normalize_text(artist.name):
            raise ValueError(
                f"Nome artista normalizzato non valido: {artist.uri}"
            )

    for place in places:
        if place.normalized_name != normalize_text(place.name):
            raise ValueError(
                f"Nome luogo normalizzato non valido: {place.uri}"
            )

        if place.city != "Napoli":
            raise ValueError(
                f"Città non valida per il luogo {place.uri}: "
                f"{place.city}"
            )

    for artwork in artworks:
        if artwork.normalized_title != normalize_text(artwork.title):
            raise ValueError(
                f"Titolo normalizzato non valido: {artwork.uri}"
            )

        if artwork.artist_uri not in artist_uris:
            raise ValueError(
                f"Artista inesistente per l'opera {artwork.uri}"
            )

        if artwork.place_uri not in place_uris:
            raise ValueError(
                f"Luogo inesistente per l'opera {artwork.uri}"
            )

        if artwork.city != "Napoli":
            raise ValueError(
                f"Città non valida per l'opera {artwork.uri}"
            )


def main() -> None:
    datasets = [
        load_json(path)
        for path in INPUT_PATHS
    ]

    combined = merge_datasets(datasets)
    validate_knowledge(combined)

    OUTPUT_PATH.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    with OUTPUT_PATH.open("w", encoding="utf-8") as file:
        json.dump(
            combined,
            file,
            ensure_ascii=False,
            indent=2,
        )
        file.write("\n")

    print(f"Dataset unificato salvato in: {OUTPUT_PATH}")
    print(f"Artisti: {len(combined['artists'])}")
    print(f"Luoghi unici: {len(combined['places'])}")
    print(f"Opere: {len(combined['artworks'])}")


if __name__ == "__main__":
    main()
