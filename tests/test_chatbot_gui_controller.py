import unittest
from unittest.mock import MagicMock

from src.gui.chatbot_gui_controller import (
    ChatbotGuiController,
)


class ChatbotGuiControllerTest(unittest.TestCase):
    def setUp(self) -> None:
        self.chatbot_service = MagicMock()
        self.speech_to_text = MagicMock()
        self.text_to_speech = MagicMock()

        self.response = MagicMock()
        self.response.text = "Risposta del chatbot."
        self.chatbot_service.process.return_value = (
            self.response
        )

        self.controller = ChatbotGuiController(
            chatbot_service=self.chatbot_service,
            speech_to_text=self.speech_to_text,
            text_to_speech=self.text_to_speech,
            session_id="session-1",
        )

    def test_submits_text_and_speaks_response(
        self,
    ) -> None:
        result = self.controller.submit_text(
            "  Dove si trova l'opera?  "
        )

        self.assertIs(result, self.response)
        self.chatbot_service.process.assert_called_once_with(
            session_id="session-1",
            text="Dove si trova l'opera?",
        )
        self.text_to_speech.speak.assert_called_once_with(
            "Risposta del chatbot."
        )

    def test_can_submit_without_immediate_speech(
        self,
    ) -> None:
        result = self.controller.submit_text(
            "Dove si trova l'opera?",
            speak_response=False,
        )

        self.assertIs(result, self.response)
        self.text_to_speech.speak.assert_not_called()

    def test_can_speak_response_separately(
        self,
    ) -> None:
        self.controller.speak_response(
            self.response
        )

        self.text_to_speech.speak.assert_called_once_with(
            "Risposta del chatbot."
        )

    def test_listens_and_submits_transcription(
        self,
    ) -> None:
        self.speech_to_text.listen.return_value = (
            "Parlami di Caravaggio"
        )

        transcription, response = (
            self.controller.listen_and_submit()
        )

        self.assertEqual(
            transcription,
            "Parlami di Caravaggio",
        )
        self.assertIs(response, self.response)
        self.speech_to_text.listen.assert_called_once_with()
        self.chatbot_service.process.assert_called_once_with(
            session_id="session-1",
            text="Parlami di Caravaggio",
        )

    def test_rejects_empty_text(self) -> None:
        with self.assertRaises(ValueError):
            self.controller.submit_text("   ")

        self.chatbot_service.process.assert_not_called()
        self.text_to_speech.speak.assert_not_called()

    def test_replaces_speech_to_text_engine(
        self,
    ) -> None:
        new_speech_to_text = MagicMock()

        self.controller.set_speech_to_text(
            new_speech_to_text
        )
        new_speech_to_text.listen.return_value = "Nuova domanda"

        transcription, _ = (
            self.controller.listen_and_submit()
        )

        self.assertEqual(
            transcription,
            "Nuova domanda",
        )
        new_speech_to_text.listen.assert_called_once_with()
        self.speech_to_text.listen.assert_not_called()

    def test_rejects_empty_session_id(self) -> None:
        with self.assertRaises(ValueError):
            ChatbotGuiController(
                chatbot_service=self.chatbot_service,
                speech_to_text=self.speech_to_text,
                text_to_speech=self.text_to_speech,
                session_id="   ",
            )


if __name__ == "__main__":
    unittest.main()
