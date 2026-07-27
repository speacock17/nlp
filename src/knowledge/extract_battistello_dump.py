import bz2
import json
import re
from collections import defaultdict
from pathlib import Path
from typing import Any


ARTIST_URI = (
    "http://it.dbpedia.org/resource/"
    "Battistello_Caracciolo"
)
NAPLES_URI = "http://it.dbpedia.org/resource/Napoli"

AUTHOR_PREDICATE = "http://dbpedia.org/ontology/author"
LOCATION_PREDICATE = "http://dbpedia.org/ontology/location"
BIRTH_PLACE_PREDICATE = "http://dbpedia.org/ontology/birthPlace"
DEATH_PLACE_PREDICATE = "http://dbpedia.org/ontology/deathPlace"
NAME_PREDICATES = (
    (
        "http://xmlns.com/foaf/0.1/name",
        "foaf:name",
    ),
    (
        "http://dbpedia.org/ontology/name",
        "dbo:name",
    ),
)
LABEL_PREDICATE = "http://www.w3.org/2000/01/rdf-schema#label"

OBJECT_TRIPLE_PATTERN = re.compile(
    r'^<([^>]+)> <([^>]+)> <([^>]+)> \.$'
)

LITERAL_TRIPLE_PATTERN = re.compile(
    r'^<([^>]+)> <([^>]+)> '
    r'("(?:[^"\\]|\\.)*")'
    r'(?:@([A-Za-z-]+)|\^\^<([^>]+)>)? \.$'
)


def append_unique(
    mapping: dict[str, dict[str, list[dict[str, str | None]]]],
    subject: str,
    predicate: str,
    value: dict[str, str | None],
) -> None:
    values = mapping[subject][predicate]

    if value not in values:
        values.append(value)


def read_authored_artworks(objects_path: Path) -> set[str]:
    artwork_uris: set[str] = set()

    with bz2.open(objects_path, mode="rt", encoding="utf-8") as file:
        for line in file:
            match = OBJECT_TRIPLE_PATTERN.match(line.rstrip())

            if not match:
                continue

            subject, predicate, obj = match.groups()

            if predicate == AUTHOR_PREDICATE and obj == ARTIST_URI:
                artwork_uris.add(subject)

    return artwork_uris


def read_artist_places(
    objects_path: Path,
) -> dict[str, str | None]:
    result: dict[str, str | None] = {
        "birth_place_uri": None,
        "death_place_uri": None,
    }

    with bz2.open(objects_path, mode="rt", encoding="utf-8") as file:
        for line in file:
            match = OBJECT_TRIPLE_PATTERN.match(line.rstrip())

            if not match:
                continue

            subject, predicate, obj = match.groups()

            if subject != ARTIST_URI:
                continue

            if predicate == BIRTH_PLACE_PREDICATE:
                result["birth_place_uri"] = obj

            elif predicate == DEATH_PLACE_PREDICATE:
                result["death_place_uri"] = obj

    return result


def read_locations(
    objects_path: Path,
    artwork_uris: set[str],
) -> dict[str, list[str]]:
    locations: dict[str, list[str]] = defaultdict(list)

    with bz2.open(objects_path, mode="rt", encoding="utf-8") as file:
        for line in file:
            match = OBJECT_TRIPLE_PATTERN.match(line.rstrip())

            if not match:
                continue

            subject, predicate, obj = match.groups()

            if (
                subject in artwork_uris
                and predicate == LOCATION_PREDICATE
                and obj not in locations[subject]
            ):
                locations[subject].append(obj)

    return locations


def read_literal_properties(
    literals_path: Path,
    resource_uris: set[str],
) -> dict[str, dict[str, list[dict[str, str | None]]]]:
    properties: dict[
        str,
        dict[str, list[dict[str, str | None]]],
    ] = defaultdict(lambda: defaultdict(list))

    with bz2.open(literals_path, mode="rt", encoding="utf-8") as file:
        for line in file:
            match = LITERAL_TRIPLE_PATTERN.match(line.rstrip())

            if not match:
                continue

            subject, predicate, encoded_value, language, datatype = (
                match.groups()
            )

            if subject not in resource_uris:
                continue

            append_unique(
                properties,
                subject,
                predicate,
                {
                    "value": json.loads(encoded_value),
                    "language": language,
                    "datatype": datatype,
                },
            )

    return properties


def read_italian_labels(
    labels_path: Path,
    resource_uris: set[str],
) -> dict[str, list[str]]:
    labels: dict[str, list[str]] = defaultdict(list)

    with bz2.open(labels_path, mode="rt", encoding="utf-8") as file:
        for line in file:
            match = LITERAL_TRIPLE_PATTERN.match(line.rstrip())

            if not match:
                continue

            subject, predicate, encoded_value, language, _ = match.groups()

            if subject not in resource_uris:
                continue

            if predicate != LABEL_PREDICATE or language != "it":
                continue

            label = json.loads(encoded_value)

            if label not in labels[subject]:
                labels[subject].append(label)

    return labels


def literal_values(
    properties: dict[str, list[dict[str, str | None]]],
    predicate: str,
    language: str | None = None,
) -> list[str]:
    values: list[str] = []

    for item in properties.get(predicate, []):
        if language is not None and item["language"] != language:
            continue

        value = item["value"]

        if value is not None and value not in values:
            values.append(value)

    return values


def choose_name(
    uri: str,
    labels: dict[str, list[str]],
    properties: dict[
        str,
        dict[str, list[dict[str, str | None]]],
    ],
) -> tuple[str | None, str | None]:
    italian_labels = labels.get(uri, [])

    if italian_labels:
        return italian_labels[0], "rdfs:label"

    for predicate, source_name in NAME_PREDICATES:
        names = literal_values(
            properties.get(uri, {}),
            predicate,
            language="it",
        )

        if names:
            return names[0], source_name

    return None, None


def extract(
    objects_path: Path,
    literals_path: Path,
    labels_path: Path,
) -> dict[str, Any]:
    for path in (objects_path, literals_path, labels_path):
        if not path.is_file():
            raise FileNotFoundError(f"Dataset non trovato: {path}")

    artwork_uris = read_authored_artworks(objects_path)
    artist_places = read_artist_places(objects_path)
    locations = read_locations(objects_path, artwork_uris)

    place_uris = {
        location_uri
        for artwork_locations in locations.values()
        for location_uri in artwork_locations
        if location_uri != NAPLES_URI
    }

    resource_uris = {
        ARTIST_URI,
        NAPLES_URI,
        *artwork_uris,
        *place_uris,
    }

    properties = read_literal_properties(
        literals_path,
        resource_uris,
    )
    labels = read_italian_labels(
        labels_path,
        resource_uris,
    )

    artist_name, artist_name_source = choose_name(
        ARTIST_URI,
        labels,
        properties,
    )

    artworks: list[dict[str, Any]] = []

    for artwork_uri in sorted(artwork_uris):
        title, title_source = choose_name(
            artwork_uri,
            labels,
            properties,
        )

        artwork_locations = sorted(locations.get(artwork_uri, []))
        venue_uris = [
            uri
            for uri in artwork_locations
            if uri != NAPLES_URI
        ]

        artworks.append(
            {
                "uri": artwork_uri,
                "title": title,
                "title_source": title_source,
                "artist_uri": ARTIST_URI,
                "location_uris": artwork_locations,
                "venue_uris": venue_uris,
                "is_naples_candidate": NAPLES_URI in artwork_locations,
                "literal_properties": properties.get(artwork_uri, {}),
            }
        )

    places: list[dict[str, Any]] = []

    for place_uri in sorted(place_uris):
        place_name, place_name_source = choose_name(
            place_uri,
            labels,
            properties,
        )

        places.append(
            {
                "uri": place_uri,
                "name": place_name,
                "name_source": place_name_source,
                "literal_properties": properties.get(place_uri, {}),
            }
        )

    return {
        "metadata": {
            "source": "DBpedia Italian dumps",
            "objects_version": "2020.08.01",
            "literals_version": "2020.08.01",
            "labels_version": "2020.07.01",
        },
        "artist": {
            "uri": ARTIST_URI,
            "name": artist_name,
            "name_source": artist_name_source,
            "birth_place_uri": artist_places["birth_place_uri"],
            "death_place_uri": artist_places["death_place_uri"],
            "literal_properties": properties.get(ARTIST_URI, {}),
        },
        "artworks": artworks,
        "places": places,
    }


def main() -> None:
    base_path = Path("data/raw/dbpedia/databus")

    data = extract(
        objects_path=base_path
        / "mappingbased-objects_lang=it.ttl.bz2",
        literals_path=base_path
        / "mappingbased-literals_lang=it.ttl.bz2",
        labels_path=base_path
        / "labels_lang=it.ttl.bz2",
    )

    output_path = Path(
        "data/raw/dbpedia/battistello_it_dump.json"
    )
    output_path.parent.mkdir(parents=True, exist_ok=True)

    with output_path.open("w", encoding="utf-8") as file:
        json.dump(data, file, ensure_ascii=False, indent=2)
        file.write("\n")

    print(f"Dataset salvato in: {output_path}")
    print(f"Opere totali: {len(data['artworks'])}")
    print(
        "Opere candidate a Napoli: "
        f"{sum(a['is_naples_candidate'] for a in data['artworks'])}"
    )
    print(f"Luoghi distinti: {len(data['places'])}")


if __name__ == "__main__":
    main()
