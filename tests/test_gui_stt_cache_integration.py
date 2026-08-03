import unittest
from unittest.mock import MagicMock, patch

import gui_main


class GuiSttCacheIntegrationTest(unittest.TestCase):
    @patch("gui_main.tk.Tk")
    @patch("gui_main.ChatbotWindow")
    @patch("gui_main.SpeechToTextCache")
    @patch("gui_main.TextToSpeech")
    @patch("gui_main.create_speech_to_text")
    @patch("gui_main.ChatbotGuiController")
    @patch("gui_main.create_chatbot_service")
    @patch("gui_main.Neo4jMemoryRepository")
    @patch("gui_main.Neo4jKnowledgeRepository")
    def test_passes_cached_stt_engines_to_window(
        self,
        knowledge_repository_class,
        memory_repository_class,
        chatbot_service_class,
        controller_class,
        create_speech_to_text_mock,
        text_to_speech_class,
        cache_class,
        window_class,
        tk_class,
    ) -> None:
        knowledge_repository = MagicMock()
        memory_repository = MagicMock()
        chatbot_service = MagicMock()
        controller = MagicMock()
        speech_to_text = MagicMock()
        text_to_speech = MagicMock()
        cache = MagicMock()
        root = MagicMock()

        knowledge_repository.check_health.return_value = True
        knowledge_repository_class.from_env.return_value = (
            knowledge_repository
        )
        memory_repository_class.from_env.return_value = (
            memory_repository
        )
        chatbot_service_class.return_value = chatbot_service
        controller_class.return_value = controller
        create_speech_to_text_mock.return_value = (
            speech_to_text
        )
        text_to_speech_class.return_value = text_to_speech
        cache_class.return_value = cache
        tk_class.return_value = root

        gui_main.main()

        cache_class.assert_called_once_with(
            factory=create_speech_to_text_mock,
            initial_engine_name="whisper",
            initial_engine=speech_to_text,
        )

        window_class.assert_called_once_with(
            root=root,
            controller=controller,
            speech_to_text_cache=cache,
            default_engine="whisper",
        )


if __name__ == "__main__":
    unittest.main()
