import unittest
from dataclasses import fields

from src.core.constants import (
    FUZZY_MATCH_ACCEPTED_THRESHOLD,
    FUZZY_MATCH_AMBIGUOUS_THRESHOLD,
)
from src.core.enums import ClaimType, EntityType, InconsistencyType, Intent
from src.core.interfaces import KnowledgeRepository, MemoryRepository
from src.core.models import (
    Artist,
    Artwork,
    BotResponse,
    Claim,
    ConversationTurn,
    DialogueState,
    EntityMention,
    Inconsistency,
    NLUResult,
    Place,
)


class SharedContractsTest(unittest.TestCase):
    def test_intent_values(self) -> None:
        self.assertEqual(
            [intent.value for intent in Intent],
            [
                "list_artworks_by_artist",
                "artwork_location",
                "artwork_author",
                "artwork_date",
                "artwork_description",
                "artist_info",
                "list_places",
                "place_artworks",
                "compare_artists",
                "follow_up",
                "out_of_scope",
                "unknown",
            ],
        )

    def test_entity_type_values(self) -> None:
        self.assertEqual(
            [entity_type.value for entity_type in EntityType],
            ["artist", "artwork", "place", "city", "date", "ordinal"],
        )

    def test_claim_type_values(self) -> None:
        self.assertEqual(
            [claim_type.value for claim_type in ClaimType],
            ["artwork_author", "artwork_location", "artwork_date"],
        )

    def test_inconsistency_type_values(self) -> None:
        self.assertEqual(
            [item.value for item in InconsistencyType],
            [
                "wrong_author",
                "wrong_location",
                "impossible_date",
                "entity_not_found",
                "ambiguous_entity",
            ],
        )

    def test_model_fields(self) -> None:
        expected_fields = {
            Artist: [
                "uri", "name", "normalized_name", "full_name", "birth_date",
                "death_date", "birth_place", "death_place", "description",
                "image_url", "source",
            ],
            Place: [
                "uri", "name", "normalized_name", "city", "place_type",
                "address", "latitude", "longitude", "description",
                "image_url", "source",
            ],
            Artwork: [
                "uri", "title", "normalized_title", "artist_uri",
                "artist_name", "place_uri", "place_name", "city", "year",
                "completion_date", "medium", "subject", "description",
                "image_url", "source",
            ],
            EntityMention: [
                "entity_type", "text", "canonical_name", "uri", "confidence",
                "start", "end",
            ],
            Claim: [
                "claim_type", "subject_uri", "claimed_value", "confidence",
            ],
            NLUResult: [
                "raw_text", "normalized_text", "intent",
                "intent_confidence", "entities", "claims",
            ],
            Inconsistency: [
                "inconsistency_type", "message", "claimed_value",
                "correct_value",
            ],
            DialogueState: [
                "session_id", "turn_index", "last_intent",
                "current_artist_uri", "current_artwork_uri",
                "current_place_uri", "last_result_uris",
                "pending_clarification", "clarification_options",
                "updated_at",
            ],
            ConversationTurn: [
                "session_id", "turn_index", "user_text", "assistant_text",
                "intent", "timestamp", "entities", "inconsistency",
            ],
            BotResponse: [
                "text", "intent", "artworks", "artists", "places",
                "inconsistency", "needs_clarification",
                "clarification_options",
            ],
        }

        for model, expected in expected_fields.items():
            with self.subTest(model=model.__name__):
                self.assertEqual(
                    [field.name for field in fields(model)],
                    expected,
                )

    def test_fuzzy_thresholds(self) -> None:
        self.assertEqual(FUZZY_MATCH_ACCEPTED_THRESHOLD, 0.90)
        self.assertEqual(FUZZY_MATCH_AMBIGUOUS_THRESHOLD, 0.75)

    def test_knowledge_repository_methods(self) -> None:
        self.assertEqual(
            KnowledgeRepository.__abstractmethods__,
            {
                "check_health",
                "get_artwork_by_uri",
                "get_artwork_by_title",
                "search_artworks",
                "list_artworks_by_artist",
                "list_artworks_by_place",
                "get_artist_by_name",
                "get_artist_by_uri",
                "search_artists",
                "get_place_by_name",
                "list_places",
                "search_places",
            },
        )

    def test_memory_repository_methods(self) -> None:
        self.assertEqual(
            MemoryRepository.__abstractmethods__,
            {
                "create_session",
                "load_state",
                "save_state",
                "save_turn",
                "get_recent_turns",
                "clear_session",
            },
        )


if __name__ == "__main__":
    unittest.main()
