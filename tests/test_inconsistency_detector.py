import unittest

from src.core.enums import (
    ClaimType,
    InconsistencyType,
)
from src.core.models import Claim, Inconsistency
from src.database.mock_knowledge_repository import (
    MockKnowledgeRepository,
)
from src.nlp.inconsistency_detector import (
    InconsistencyDetector,
)


class InconsistencyDetectorTest(unittest.TestCase):
    def setUp(self) -> None:
        self.repository = MockKnowledgeRepository()
        self.detector = InconsistencyDetector(
            self.repository
        )
        self.artwork_uri = (
            "http://dbpedia.org/resource/"
            "The_Martyrdom_of_Saint_Ursula_"
            "(Caravaggio)"
        )

    def test_wrong_author_is_detected(self) -> None:
        inconsistency = self.detector.detect(
            [
                Claim(
                    claim_type=ClaimType.ARTWORK_AUTHOR,
                    subject_uri=self.artwork_uri,
                    claimed_value="Battistello Caracciolo",
                    confidence=1.0,
                )
            ]
        )

        self.assertIsInstance(
            inconsistency,
            Inconsistency,
        )
        self.assertEqual(
            inconsistency.inconsistency_type,
            InconsistencyType.WRONG_AUTHOR,
        )
        self.assertEqual(
            inconsistency.claimed_value,
            "Battistello Caracciolo",
        )
        self.assertEqual(
            inconsistency.correct_value,
            "Caravaggio",
        )

    def test_correct_author_has_no_inconsistency(
        self,
    ) -> None:
        inconsistency = self.detector.detect(
            [
                Claim(
                    claim_type=ClaimType.ARTWORK_AUTHOR,
                    subject_uri=self.artwork_uri,
                    claimed_value="Caravaggio",
                    confidence=1.0,
                )
            ]
        )

        self.assertIsNone(inconsistency)

    def test_wrong_location_is_detected(self) -> None:
        inconsistency = self.detector.detect(
            [
                Claim(
                    claim_type=ClaimType.ARTWORK_LOCATION,
                    subject_uri=self.artwork_uri,
                    claimed_value=(
                        "Museo nazionale di Capodimonte"
                    ),
                    confidence=1.0,
                )
            ]
        )

        self.assertEqual(
            inconsistency.inconsistency_type,
            InconsistencyType.WRONG_LOCATION,
        )
        self.assertEqual(
            inconsistency.correct_value,
            "Palazzo Zevallos",
        )

    def test_correct_location_has_no_inconsistency(
        self,
    ) -> None:
        inconsistency = self.detector.detect(
            [
                Claim(
                    claim_type=ClaimType.ARTWORK_LOCATION,
                    subject_uri=self.artwork_uri,
                    claimed_value="Palazzo Zevallos",
                    confidence=1.0,
                )
            ]
        )

        self.assertIsNone(inconsistency)

    def test_wrong_date_is_detected(self) -> None:
        inconsistency = self.detector.detect(
            [
                Claim(
                    claim_type=ClaimType.ARTWORK_DATE,
                    subject_uri=self.artwork_uri,
                    claimed_value="1607",
                    confidence=1.0,
                )
            ]
        )

        self.assertEqual(
            inconsistency.inconsistency_type,
            InconsistencyType.IMPOSSIBLE_DATE,
        )
        self.assertEqual(
            inconsistency.claimed_value,
            "1607",
        )
        self.assertEqual(
            inconsistency.correct_value,
            "1610",
        )

    def test_correct_date_has_no_inconsistency(
        self,
    ) -> None:
        inconsistency = self.detector.detect(
            [
                Claim(
                    claim_type=ClaimType.ARTWORK_DATE,
                    subject_uri=self.artwork_uri,
                    claimed_value="1610",
                    confidence=1.0,
                )
            ]
        )

        self.assertIsNone(inconsistency)

    def test_missing_artwork_is_detected(self) -> None:
        inconsistency = self.detector.detect(
            [
                Claim(
                    claim_type=ClaimType.ARTWORK_AUTHOR,
                    subject_uri="urn:artwork:not-found",
                    claimed_value="Caravaggio",
                    confidence=1.0,
                )
            ]
        )

        self.assertEqual(
            inconsistency.inconsistency_type,
            InconsistencyType.ENTITY_NOT_FOUND,
        )
        self.assertEqual(
            inconsistency.claimed_value,
            "urn:artwork:not-found",
        )
        self.assertIsNone(
            inconsistency.correct_value
        )

    def test_claim_without_subject_is_detected(
        self,
    ) -> None:
        inconsistency = self.detector.detect(
            [
                Claim(
                    claim_type=ClaimType.ARTWORK_AUTHOR,
                    subject_uri=None,
                    claimed_value="Caravaggio",
                    confidence=1.0,
                )
            ]
        )

        self.assertEqual(
            inconsistency.inconsistency_type,
            InconsistencyType.ENTITY_NOT_FOUND,
        )

    def test_empty_claims_have_no_inconsistency(
        self,
    ) -> None:
        self.assertIsNone(
            self.detector.detect([])
        )


if __name__ == "__main__":
    unittest.main()
