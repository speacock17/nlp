import unittest
from unittest.mock import MagicMock, patch

from src.database.mock_knowledge_repository import (
    MockKnowledgeRepository,
)
from src.database.mock_memory_repository import (
    MockMemoryRepository,
)
from src.dialogue.chatbot_service import ChatbotService
from src.dialogue.chatbot_service_factory import (
    create_chatbot_service,
)
from src.dialogue.hybrid_chatbot_service import (
    HybridChatbotService,
)


class ChatbotServiceFactoryTest(unittest.TestCase):
    def setUp(self) -> None:
        self.knowledge_repository = (
            MockKnowledgeRepository()
        )
        self.memory_repository = MockMemoryRepository()

    def test_creates_deterministic_service_when_disabled(
        self,
    ) -> None:
        service = create_chatbot_service(
            knowledge_repository=(
                self.knowledge_repository
            ),
            memory_repository=self.memory_repository,
            llm_enabled=False,
        )

        self.assertIsInstance(
            service,
            ChatbotService,
        )
        self.assertNotIsInstance(
            service,
            HybridChatbotService,
        )

    def test_creates_hybrid_service_when_enabled(
        self,
    ) -> None:
        llm_client = MagicMock()

        service = create_chatbot_service(
            knowledge_repository=(
                self.knowledge_repository
            ),
            memory_repository=self.memory_repository,
            llm_enabled=True,
            llm_client=llm_client,
        )

        self.assertIsInstance(
            service,
            HybridChatbotService,
        )

    @patch.dict(
        "os.environ",
        {"LLM_ENABLED": "true"},
        clear=False,
    )
    def test_reads_enabled_flag_from_environment(
        self,
    ) -> None:
        service = create_chatbot_service(
            knowledge_repository=(
                self.knowledge_repository
            ),
            memory_repository=self.memory_repository,
            llm_client=MagicMock(),
        )

        self.assertIsInstance(
            service,
            HybridChatbotService,
        )

    @patch.dict(
        "os.environ",
        {"LLM_ENABLED": "false"},
        clear=False,
    )
    def test_reads_disabled_flag_from_environment(
        self,
    ) -> None:
        service = create_chatbot_service(
            knowledge_repository=(
                self.knowledge_repository
            ),
            memory_repository=self.memory_repository,
        )

        self.assertIsInstance(
            service,
            ChatbotService,
        )

    def test_rejects_invalid_environment_flag(
        self,
    ) -> None:
        with patch.dict(
            "os.environ",
            {"LLM_ENABLED": "forse"},
            clear=False,
        ):
            with self.assertRaises(ValueError):
                create_chatbot_service(
                    knowledge_repository=(
                        self.knowledge_repository
                    ),
                    memory_repository=(
                        self.memory_repository
                    ),
                )


if __name__ == "__main__":
    unittest.main()
