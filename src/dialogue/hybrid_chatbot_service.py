from dataclasses import replace

from src.core.enums import Intent
from src.core.interfaces import (
    KnowledgeRepository,
    MemoryRepository,
)
from src.core.models import NLUResult
from src.dialogue.context_resolver import ContextResolver
from src.dialogue.dialogue_manager import DialogueManager
from src.dialogue.response_generator import ResponseGenerator
from src.llm.agent_result_mapper import AgentResultMapper
from src.nlp.inconsistency_detector import (
    InconsistencyDetector,
)
from src.nlp.nlu_pipeline import NLUPipeline


class HybridChatbotService:
    def __init__(
        self,
        knowledge_repository: KnowledgeRepository,
        memory_repository: MemoryRepository,
        agent,
        fallback_service,
    ) -> None:
        self._agent = agent
        self._fallback_service = fallback_service

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
        self._result_mapper = AgentResultMapper()

    def process(
        self,
        session_id: str,
        text: str,
    ):
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

        if inconsistency is not None:
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

        agent_prompt = self._build_agent_prompt(
            resolved_result
        )

        try:
            agent_result = self._agent.run(
                agent_prompt
            )

            response = self._result_mapper.map(
                result=agent_result,
                preferred_intent=(
                    self._preferred_intent(
                        resolved_result
                    )
                ),
            )
        except Exception:
            return self._fallback_service.process(
                session_id=session_id,
                text=text,
            )

        recorded_result = replace(
            resolved_result,
            intent=response.intent,
            intent_confidence=max(
                resolved_result.intent_confidence,
                0.90,
            ),
        )

        self._dialogue_manager.record_turn(
            session_id=session_id,
            nlu_result=recorded_result,
            response=response,
        )

        return response

    @staticmethod
    def _preferred_intent(
        nlu_result: NLUResult,
    ) -> Intent | None:
        if nlu_result.intent in {
            Intent.UNKNOWN,
            Intent.FOLLOW_UP,
        }:
            return None

        return nlu_result.intent

    @staticmethod
    def _build_agent_prompt(
        nlu_result: NLUResult,
    ) -> str:
        lines = [
            "Domanda dell'utente:",
            nlu_result.raw_text,
        ]

        if nlu_result.entities:
            lines.extend(
                [
                    "",
                    (
                        "Contesto conversazionale gi? "
                        "risolto dal sistema:"
                    ),
                ]
            )

            for entity in nlu_result.entities:
                name = (
                    entity.canonical_name
                    or entity.text
                )

                lines.append(
                    f"- {entity.entity_type.value}: "
                    f"{name}"
                )

        return "\n".join(lines)
