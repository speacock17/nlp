from src.core.enums import EntityType, Intent
from src.core.interfaces import KnowledgeRepository
from src.core.models import NLUResult
from src.nlp.claim_extractor import ClaimExtractor
from src.nlp.entity_linker import EntityLinker
from src.nlp.intent_classifier import classify_intent
from src.nlp.preprocessing import preprocess_question


class NLUPipeline:
    def __init__(
        self,
        knowledge_repository: KnowledgeRepository,
    ) -> None:
        self._entity_linker = EntityLinker(
            knowledge_repository
        )
        self._claim_extractor = ClaimExtractor()

    def analyze(
        self,
        text: str,
    ) -> NLUResult:
        normalized_text = preprocess_question(text)

        intent, intent_confidence = classify_intent(
            text
        )

        entities = self._entity_linker.link(text)

        if (
            intent == Intent.UNKNOWN
            and normalized_text.startswith("parlami di ")
            and any(
                entity.entity_type == EntityType.ARTIST
                for entity in entities
            )
        ):
            intent = Intent.ARTIST_INFO
            intent_confidence = 0.90

        claims = self._claim_extractor.extract(
            text,
            entities,
        )

        return NLUResult(
            raw_text=text,
            normalized_text=normalized_text,
            intent=intent,
            intent_confidence=intent_confidence,
            entities=entities,
            claims=claims,
        )
