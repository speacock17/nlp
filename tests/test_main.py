import unittest
from unittest.mock import MagicMock, patch
from uuid import UUID

import main as app_main


class MainTest(unittest.TestCase):
    @patch("main.uuid4")
    @patch("main.TextToSpeech")
    @patch("main.create_speech_to_text")
    @patch("main.getenv")
    @patch("main.load_dotenv")
    @patch("main.VoiceChatbotApp")
    @patch("main.ChatbotService")
    @patch("main.Neo4jMemoryRepository")
    @patch("main.Neo4jKnowledgeRepository")
    def test_builds_and_runs_voice_chatbot(
        self,
        knowledge_repository_class,
        memory_repository_class,
        chatbot_service_class,
        voice_app_class,
        load_dotenv_mock,
        getenv_mock,
        create_speech_to_text_mock,
        text_to_speech_class,
        uuid4_mock,
    ) -> None:
        knowledge_repository = MagicMock()
        memory_repository = MagicMock()
        chatbot_service = MagicMock()
        speech_to_text = MagicMock()
        text_to_speech = MagicMock()
        voice_app = MagicMock()

        knowledge_repository.check_health.return_value = True

        knowledge_repository_class.from_env.return_value = (
            knowledge_repository
        )
        memory_repository_class.from_env.return_value = (
            memory_repository
        )
        chatbot_service_class.return_value = chatbot_service
        create_speech_to_text_mock.return_value = (
            speech_to_text
        )
        text_to_speech_class.return_value = text_to_speech
        voice_app_class.return_value = voice_app
        getenv_mock.return_value = "whisper"

        uuid4_mock.return_value = UUID(
            "00000000-0000-0000-0000-000000000001"
        )

        app_main.main()

        load_dotenv_mock.assert_called_once_with()
        getenv_mock.assert_called_once_with(
            "STT_ENGINE",
            "whisper",
        )
        create_speech_to_text_mock.assert_called_once_with(
            "whisper"
        )
        chatbot_service_class.assert_called_once_with(
            knowledge_repository=knowledge_repository,
            memory_repository=memory_repository,
        )
        voice_app_class.assert_called_once_with(
            chatbot_service=chatbot_service,
            speech_to_text=speech_to_text,
            text_to_speech=text_to_speech,
            session_id=(
                "00000000-0000-0000-0000-000000000001"
            ),
        )
        voice_app.run.assert_called_once_with()
        knowledge_repository.close.assert_called_once_with()
        memory_repository.close.assert_called_once_with()

    @patch("main.TextToSpeech")
    @patch("main.create_speech_to_text")
    @patch("main.VoiceChatbotApp")
    @patch("main.ChatbotService")
    @patch("main.Neo4jMemoryRepository")
    @patch("main.Neo4jKnowledgeRepository")
    def test_closes_repositories_when_database_is_unhealthy(
        self,
        knowledge_repository_class,
        memory_repository_class,
        chatbot_service_class,
        voice_app_class,
        create_speech_to_text_mock,
        text_to_speech_class,
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
            app_main.main()

        chatbot_service_class.assert_not_called()
        voice_app_class.assert_not_called()
        create_speech_to_text_mock.assert_not_called()
        text_to_speech_class.assert_not_called()
        knowledge_repository.close.assert_called_once_with()
        memory_repository.close.assert_called_once_with()


if __name__ == "__main__":
    unittest.main()
