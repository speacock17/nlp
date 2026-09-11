import unittest
from unittest.mock import MagicMock, patch
from uuid import UUID

import gui_main


class GuiMainTest(unittest.TestCase):
    @patch("gui_main.uuid4")
    @patch("gui_main.ctk.CTk")
    @patch("gui_main.TextToSpeech")
    @patch("gui_main.create_speech_to_text")
    @patch("gui_main.ChatbotWindow")
    @patch("gui_main.ChatbotGuiController")
    @patch("gui_main.create_chatbot_service")
    @patch("gui_main.Neo4jMemoryRepository")
    @patch("gui_main.Neo4jKnowledgeRepository")
    def test_builds_and_runs_gui(
        self,
        knowledge_repository_class,
        memory_repository_class,
        chatbot_service_class,
        controller_class,
        window_class,
        create_speech_to_text_mock,
        text_to_speech_class,
        tk_class,
        uuid4_mock,
    ) -> None:
        knowledge_repository = MagicMock()
        memory_repository = MagicMock()
        chatbot_service = MagicMock()
        controller = MagicMock()
        root = MagicMock()
        speech_to_text = MagicMock()
        text_to_speech = MagicMock()

        knowledge_repository.check_health.return_value = True

        knowledge_repository_class.from_env.return_value = (
            knowledge_repository
        )
        memory_repository_class.from_env.return_value = (
            memory_repository
        )
        chatbot_service_class.return_value = chatbot_service
        controller_class.return_value = controller
        tk_class.return_value = root
        create_speech_to_text_mock.return_value = (
            speech_to_text
        )
        text_to_speech_class.return_value = text_to_speech

        uuid4_mock.return_value = UUID(
            "00000000-0000-0000-0000-000000000002"
        )

        gui_main.main()

        create_speech_to_text_mock.assert_called_once_with(
            "whisper"
        )
        controller_class.assert_called_once_with(
            chatbot_service=chatbot_service,
            speech_to_text=speech_to_text,
            text_to_speech=text_to_speech,
            session_id=(
                "00000000-0000-0000-0000-000000000002"
            ),
        )
        window_class.assert_called_once()
        root.mainloop.assert_called_once_with()

    @patch("gui_main.Neo4jMemoryRepository")
    @patch("gui_main.Neo4jKnowledgeRepository")
    def test_closes_repositories_when_database_is_unhealthy(
        self,
        knowledge_repository_class,
        memory_repository_class,
    ) -> None:
        knowledge_repository = MagicMock()
        memory_repository = MagicMock()

        knowledge_repository.check_health.return_value = False

        knowledge_repository_class.from_env.return_value = (
            knowledge_repository
        )
        memory_repository_class.from_env.return_value = (
            memory_repository
        )

        with self.assertRaises(RuntimeError):
            gui_main.main()

        knowledge_repository.close.assert_called_once_with()
        memory_repository.close.assert_called_once_with()


if __name__ == "__main__":
    unittest.main()
