from os import getenv
from typing import Any

from src.core.interfaces import (
    KnowledgeRepository,
    MemoryRepository,
)
from src.dialogue.chatbot_service import ChatbotService
from src.dialogue.hybrid_chatbot_service import (
    HybridChatbotService,
)
from src.llm.knowledge_tools import (
    KNOWLEDGE_TOOL_SCHEMAS,
    KnowledgeToolExecutor,
)
from src.llm.ollama_llm_client import OllamaLLMClient
from src.llm.tool_calling_agent import ToolCallingAgent


def create_chatbot_service(
    knowledge_repository: KnowledgeRepository,
    memory_repository: MemoryRepository,
    llm_enabled: bool | None = None,
    llm_client: Any | None = None,
):
    enabled = (
        _read_llm_enabled()
        if llm_enabled is None
        else llm_enabled
    )

    if not isinstance(enabled, bool):
        raise TypeError(
            "llm_enabled deve essere un valore booleano"
        )

    deterministic_service = ChatbotService(
        knowledge_repository=knowledge_repository,
        memory_repository=memory_repository,
    )

    if not enabled:
        return deterministic_service

    client = (
        llm_client
        if llm_client is not None
        else OllamaLLMClient(
            model=getenv(
                "OLLAMA_MODEL",
                "qwen3:8b",
            )
        )
    )

    tool_executor = KnowledgeToolExecutor(
        knowledge_repository=knowledge_repository
    )

    agent = ToolCallingAgent(
        llm_client=client,
        tool_executor=tool_executor,
        tool_schemas=KNOWLEDGE_TOOL_SCHEMAS,
    )

    return HybridChatbotService(
        knowledge_repository=knowledge_repository,
        memory_repository=memory_repository,
        agent=agent,
        fallback_service=deterministic_service,
    )


def _read_llm_enabled() -> bool:
    raw_value = getenv(
        "LLM_ENABLED",
        "true",
    ).strip().casefold()

    if raw_value in {
        "true",
        "1",
        "yes",
        "on",
    }:
        return True

    if raw_value in {
        "false",
        "0",
        "no",
        "off",
    }:
        return False

    raise ValueError(
        "LLM_ENABLED deve essere true oppure false"
    )
