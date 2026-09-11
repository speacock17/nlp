import unittest

from src.core.enums import EntityType, Intent
from src.core.models import DialogueState, EntityMention
from src.database.mock_knowledge_repository import (
    MockKnowledgeRepository,
)
from src.database.mock_memory_repository import (
    MockMemoryRepository,
)
from src.dialogue.context_resolver import ContextResolver
from src.nlp.nlu_pipeline import NLUPipeline


class ContextResolverTest(unittest.TestCase):
    def setUp(self) -> None:
        self.knowledge_repository = (
            MockKnowledgeRepository()
        )
        self.memory_repository = MockMemoryRepository()
        self.pipeline = NLUPipeline(
            self.knowledge_repository
        )
        self.resolver = ContextResolver(
            knowledge_repository=(
                self.knowledge_repository
            ),
            memory_repository=self.memory_repository,
        )

        self.artwork = (
            self.knowledge_repository
            .get_artwork_by_title(
                "Martirio di sant'Orsola"
            )
        )
        self.artist = (
            self.knowledge_repository
            .get_artist_by_name("Caravaggio")
        )

    def test_resolves_missing_artwork_for_location(
        self,
    ) -> None:
        self.memory_repository.save_state(
            DialogueState(
                session_id="session-1",
                current_artwork_uri=self.artwork.uri,
            )
        )
        result = self.pipeline.analyze(
            "Dove si trova?"
        )

        resolved = self.resolver.resolve(
            "session-1",
            result,
        )

        self.assertEqual(
            resolved.intent,
            Intent.ARTWORK_LOCATION,
        )
        self.assertEqual(len(resolved.entities), 1)
        self.assertEqual(
            resolved.entities[0].entity_type,
            EntityType.ARTWORK,
        )
        self.assertEqual(
            resolved.entities[0].uri,
            self.artwork.uri,
        )
        self.assertEqual(
            resolved.entities[0].canonical_name,
            self.artwork.title,
        )

    def test_resolves_missing_artwork_for_author(
        self,
    ) -> None:
        self.memory_repository.save_state(
            DialogueState(
                session_id="session-1",
                current_artwork_uri=self.artwork.uri,
            )
        )
        result = self.pipeline.analyze(
            "Chi ha dipinto?"
        )

        resolved = self.resolver.resolve(
            "session-1",
            result,
        )

        self.assertEqual(
            resolved.intent,
            Intent.ARTWORK_AUTHOR,
        )
        self.assertEqual(
            resolved.entities[0].uri,
            self.artwork.uri,
        )

    def test_unknown_question_receives_current_artwork(
        self,
    ) -> None:
        self.memory_repository.save_state(
            DialogueState(
                session_id="session-1",
                current_artwork_uri=self.artwork.uri,
            )
        )
        result = self.pipeline.analyze(
            "Da chi \u00e8 stato dipinto?"
        )

        self.assertEqual(
            result.intent,
            Intent.UNKNOWN,
        )

        resolved = self.resolver.resolve(
            "session-1",
            result,
        )

        self.assertEqual(
            resolved.intent,
            Intent.UNKNOWN,
        )
        self.assertEqual(len(resolved.entities), 1)
        self.assertEqual(
            resolved.entities[0].entity_type,
            EntityType.ARTWORK,
        )
        self.assertEqual(
            resolved.entities[0].uri,
            self.artwork.uri,
        )

    def test_ordinal_selects_item_from_last_results(
        self,
    ) -> None:
        second_artwork = (
            self.knowledge_repository
            .get_artwork_by_title(
                "Sette opere di Misericordia"
            )
        )

        self.memory_repository.save_state(
            DialogueState(
                session_id="session-1",
                current_artwork_uri=self.artwork.uri,
                last_result_uris=[
                    self.artwork.uri,
                    second_artwork.uri,
                ],
            )
        )

        result = self.pipeline.analyze(
            "Dove si trova il secondo elencato?"
        )
        resolved = self.resolver.resolve(
            "session-1",
            result,
        )

        artwork_entities = [
            entity
            for entity in resolved.entities
            if entity.entity_type
            == EntityType.ARTWORK
        ]

        self.assertEqual(
            resolved.intent,
            Intent.ARTWORK_LOCATION,
        )
        self.assertEqual(
            len(artwork_entities),
            1,
        )
        self.assertEqual(
            artwork_entities[0].uri,
            second_artwork.uri,
        )

    def test_last_ordinal_selects_final_result(
        self,
    ) -> None:
        last_artwork = (
            self.knowledge_repository
            .get_artwork_by_title(
                "Sette opere di Misericordia"
            )
        )

        self.memory_repository.save_state(
            DialogueState(
                session_id="session-1",
                current_artwork_uri=self.artwork.uri,
                last_result_uris=[
                    self.artwork.uri,
                    last_artwork.uri,
                ],
            )
        )

        result = self.pipeline.analyze(
            "Dove si trova l'ultimo elencato?"
        )
        resolved = self.resolver.resolve(
            "session-1",
            result,
        )

        artwork_entities = [
            entity
            for entity in resolved.entities
            if entity.entity_type
            == EntityType.ARTWORK
        ]

        self.assertEqual(
            len(artwork_entities),
            1,
        )
        self.assertEqual(
            artwork_entities[0].uri,
            last_artwork.uri,
        )

    def test_invalid_ordinal_does_not_use_current_artwork(
        self,
    ) -> None:
        second_artwork = (
            self.knowledge_repository
            .get_artwork_by_title(
                "Sette opere di Misericordia"
            )
        )

        self.memory_repository.save_state(
            DialogueState(
                session_id="session-1",
                current_artwork_uri=self.artwork.uri,
                last_result_uris=[
                    self.artwork.uri,
                    second_artwork.uri,
                ],
            )
        )

        result = self.pipeline.analyze(
            "Dove si trova il quinto elencato?"
        )
        resolved = self.resolver.resolve(
            "session-1",
            result,
        )

        artwork_entities = [
            entity
            for entity in resolved.entities
            if entity.entity_type
            == EntityType.ARTWORK
        ]

        self.assertEqual(
            artwork_entities,
            [],
        )
        self.assertTrue(
            any(
                entity.entity_type
                == EntityType.ORDINAL
                for entity in resolved.entities
            )
        )

    def test_follow_up_uses_current_artwork(
        self,
    ) -> None:
        self.memory_repository.save_state(
            DialogueState(
                session_id="session-1",
                current_artwork_uri=self.artwork.uri,
            )
        )
        result = self.pipeline.analyze(
            "Dimmi di più"
        )

        resolved = self.resolver.resolve(
            "session-1",
            result,
        )

        self.assertEqual(
            resolved.intent,
            Intent.ARTWORK_DESCRIPTION,
        )
        self.assertEqual(
            resolved.entities[0].uri,
            self.artwork.uri,
        )

    def test_follow_up_uses_current_artist(
        self,
    ) -> None:
        self.memory_repository.save_state(
            DialogueState(
                session_id="session-1",
                current_artist_uri=self.artist.uri,
            )
        )
        result = self.pipeline.analyze(
            "Continua"
        )

        resolved = self.resolver.resolve(
            "session-1",
            result,
        )

        self.assertEqual(
            resolved.intent,
            Intent.ARTIST_INFO,
        )
        self.assertEqual(
            resolved.entities[0].entity_type,
            EntityType.ARTIST,
        )
        self.assertEqual(
            resolved.entities[0].uri,
            self.artist.uri,
        )

    def test_possessive_artworks_follow_up_uses_current_artist(
        self,
    ) -> None:
        self.memory_repository.save_state(
            DialogueState(
                session_id="session-1",
                current_artist_uri=self.artist.uri,
            )
        )
        result = self.pipeline.analyze(
            "quali sono le sue opere?"
        )

        resolved = self.resolver.resolve(
            "session-1",
            result,
        )

        self.assertEqual(
            resolved.intent,
            Intent.LIST_ARTWORKS_BY_ARTIST,
        )
        self.assertEqual(
            resolved.entities[0].entity_type,
            EntityType.ARTIST,
        )
        self.assertEqual(
            resolved.entities[0].uri,
            self.artist.uri,
        )

    def test_other_artworks_uses_current_artist(
        self,
    ) -> None:
        self.memory_repository.save_state(
            DialogueState(
                session_id="session-1",
                current_artist_uri=self.artist.uri,
            )
        )
        result = self.pipeline.analyze(
            "E le altre?"
        )

        resolved = self.resolver.resolve(
            "session-1",
            result,
        )

        self.assertEqual(
            resolved.intent,
            Intent.LIST_ARTWORKS_BY_ARTIST,
        )
        self.assertEqual(
            resolved.entities[0].uri,
            self.artist.uri,
        )

    def test_explicit_entity_has_precedence(
        self,
    ) -> None:
        other_artwork = (
            self.knowledge_repository
            .get_artwork_by_title(
                "Sette opere di Misericordia"
            )
        )
        self.memory_repository.save_state(
            DialogueState(
                session_id="session-1",
                current_artwork_uri=self.artwork.uri,
            )
        )
        result = self.pipeline.analyze(
            "Dove si trovano le Sette opere "
            "di Misericordia?"
        )

        resolved = self.resolver.resolve(
            "session-1",
            result,
        )

        artwork_entities = [
            entity
            for entity in resolved.entities
            if entity.entity_type
            == EntityType.ARTWORK
        ]

        self.assertEqual(len(artwork_entities), 1)
        self.assertEqual(
            artwork_entities[0].uri,
            other_artwork.uri,
        )

    def test_missing_session_leaves_result_unchanged(
        self,
    ) -> None:
        result = self.pipeline.analyze(
            "Dove si trova?"
        )

        resolved = self.resolver.resolve(
            "missing-session",
            result,
        )

        self.assertEqual(resolved, result)

    def test_unavailable_context_leaves_follow_up(
        self,
    ) -> None:
        self.memory_repository.save_state(
            DialogueState(
                session_id="session-1"
            )
        )
        result = self.pipeline.analyze(
            "Dimmi di più"
        )

        resolved = self.resolver.resolve(
            "session-1",
            result,
        )

        self.assertEqual(
            resolved.intent,
            Intent.FOLLOW_UP,
        )
        self.assertEqual(resolved.entities, [])


if __name__ == "__main__":
    unittest.main()
