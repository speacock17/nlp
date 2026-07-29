from src.core.interfaces import (
    KnowledgeRepository,
    MemoryRepository,
)
from src.core.models import BotResponse
from src.dialogue.context_resolver import ContextResolver
from src.dialogue.dialogue_manager import DialogueManager
from src.dialogue.response_generator import ResponseGenerator
from src.nlp.inconsistency_detector import (
    InconsistencyDetector,
)
from src.nlp.nlu_pipeline import NLUPipeline


class ChatbotService:
    def __init__(
        self,
        knowledge_repository: KnowledgeRepository,
        memory_repository: MemoryRepository,
    ) -> None:
        self._nlu_pipeline = NLUPipeline(
            knowledge_repository
        )
        self._context_resolver = ContextResolver(
            knowledge_repository=knowledge_repository,
            memory_repository=memory_repository,
        )
        self._inconsistency_detector = (
            InconsistencyDetector(
                knowledge_repository
            )
        )
        self._response_generator = ResponseGenerator(
            knowledge_repository
        )
        self._dialogue_manager = DialogueManager(
            knowledge_repository=knowledge_repository,
            memory_repository=memory_repository,
        )

    def process(
        self,
        session_id: str,
        text: str,
    ) -> BotResponse:
        nlu_result = self._nlu_pipeline.analyze(text)

        resolved_result = (
            self._context_resolver.resolve(
                session_id=session_id,
                nlu_result=nlu_result,
            )
        )

        inconsistency = (
            self._inconsistency_detector.detect(
                resolved_result.claims
            )
        )

        response = self._response_generator.generate(
            nlu_result=resolved_result,
            inconsistency=inconsistency,
        )

        self._dialogue_manager.record_turn(
            session_id=session_id,
            nlu_result=resolved_result,
            response=response,
        )

        return response
