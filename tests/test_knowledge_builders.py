import json
import unittest
from pathlib import Path
from typing import Any

from src.core.models import Artist, Artwork, Place
from src.core.normalization import normalize_text
from src.knowledge.build_battistello_knowledge import (
    build_knowledge as build_battistello_knowledge,
)
from src.knowledge.build_caravaggio_knowledge import (
    build_knowledge as build_caravaggio_knowledge,
)
from src.knowledge.build_combined_knowledge import (
    canonical_place_uri,
    merge_datasets,
    validate_knowledge,
)


class KnowledgeBuildersTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        raw_path = Path(
            "data/raw/dbpedia/battistello_it_dump.json"
        )

        with raw_path.open(encoding="utf-8") as file:
            battistello_raw = json.load(file)

        cls.battistello = build_battistello_knowledge(
            battistello_raw
        )
        cls.caravaggio = build_caravaggio_knowledge()
        cls.combined = merge_datasets(
            [cls.caravaggio, cls.battistello]
        )

    def assert_models_and_normalization(
        self,
        dataset: dict[str, Any],
    ) -> None:
        artists = [
            Artist(**item)
            for item in dataset["artists"]
        ]
        places = [
            Place(**item)
            for item in dataset["places"]
        ]
        artworks = [
            Artwork(**item)
            for item in dataset["artworks"]
        ]

        for artist in artists:
            self.assertEqual(
                artist.normalized_name,
                normalize_text(artist.name),
            )

        for place in places:
            self.assertEqual(
                place.normalized_name,
                normalize_text(place.name),
            )

        for artwork in artworks:
            self.assertEqual(
                artwork.normalized_title,
                normalize_text(artwork.title),
            )

    def test_battistello_dataset(self) -> None:
        self.assertEqual(len(self.battistello["artists"]), 1)
        self.assertEqual(len(self.battistello["places"]), 6)
        self.assertEqual(len(self.battistello["artworks"]), 8)

        self.assert_models_and_normalization(
            self.battistello
        )

    def test_caravaggio_dataset(self) -> None:
        self.assertEqual(len(self.caravaggio["artists"]), 1)
        self.assertEqual(len(self.caravaggio["places"]), 3)
        self.assertEqual(len(self.caravaggio["artworks"]), 3)

        self.assert_models_and_normalization(
            self.caravaggio
        )

    def test_place_uri_canonicalization(self) -> None:
        self.assertEqual(
            canonical_place_uri(
                "http://it.dbpedia.org/resource/"
                "Museo_nazionale_di_Capodimonte"
            ),
            "http://dbpedia.org/resource/"
            "Museo_di_Capodimonte",
        )
        self.assertEqual(
            canonical_place_uri(
                "http://it.dbpedia.org/resource/"
                "Pio_Monte_della_Misericordia"
            ),
            "http://dbpedia.org/resource/"
            "Pio_Monte_della_Misericordia",
        )

    def test_combined_dataset_counts(self) -> None:
        self.assertEqual(len(self.combined["artists"]), 2)
        self.assertEqual(len(self.combined["places"]), 7)
        self.assertEqual(len(self.combined["artworks"]), 11)

        validate_knowledge(self.combined)
        self.assert_models_and_normalization(
            self.combined
        )

    def test_combined_relations(self) -> None:
        artist_uris = {
            artist["uri"]
            for artist in self.combined["artists"]
        }
        places_by_uri = {
            place["uri"]: place
            for place in self.combined["places"]
        }

        for artwork in self.combined["artworks"]:
            self.assertIn(
                artwork["artist_uri"],
                artist_uris,
            )
            self.assertIn(
                artwork["place_uri"],
                places_by_uri,
            )
            self.assertEqual(
                artwork["place_name"],
                places_by_uri[
                    artwork["place_uri"]
                ]["name"],
            )

    def test_italian_place_aliases_are_removed(self) -> None:
        forbidden_aliases = {
            "http://it.dbpedia.org/resource/"
            "Museo_nazionale_di_Capodimonte",
            "http://it.dbpedia.org/resource/"
            "Pio_Monte_della_Misericordia",
        }

        place_uris = {
            place["uri"]
            for place in self.combined["places"]
        }

        artwork_place_uris = {
            artwork["place_uri"]
            for artwork in self.combined["artworks"]
        }

        self.assertTrue(
            forbidden_aliases.isdisjoint(place_uris)
        )
        self.assertTrue(
            forbidden_aliases.isdisjoint(
                artwork_place_uris
            )
        )

    def test_merged_places_keep_complementary_data(
        self,
    ) -> None:
        places_by_uri = {
            place["uri"]: place
            for place in self.combined["places"]
        }

        capodimonte = places_by_uri[
            "http://dbpedia.org/resource/"
            "Museo_di_Capodimonte"
        ]
        pio_monte = places_by_uri[
            "http://dbpedia.org/resource/"
            "Pio_Monte_della_Misericordia"
        ]

        self.assertEqual(
            capodimonte["address"],
            "Via Miano, 2",
        )
        self.assertIsNotNone(capodimonte["latitude"])
        self.assertIsNotNone(capodimonte["longitude"])
        self.assertIsNotNone(capodimonte["image_url"])

        self.assertEqual(
            pio_monte["address"],
            "Via dei Tribunali, 253",
        )
        self.assertIsNotNone(pio_monte["description"])
        self.assertIsNotNone(pio_monte["image_url"])


if __name__ == "__main__":
    unittest.main()
