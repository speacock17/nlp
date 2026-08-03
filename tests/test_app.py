import unittest
from unittest.mock import MagicMock

from src.app import VoiceChatbotApp
from src.core.enums import Intent
from src.core.models import BotResponse


class VoiceChatbotAppTest(unittest.TestCase):
    def setUp(self) -> None:
        self.chatbot_service = MagicMock()
        self.speech_to_text = MagicMock()
        self.text_to_speech = MagicMock()

        self.app = VoiceChatbotApp(
            chatbot_service=self.chatbot_service,
            speech_to_text=self.speech_to_text,
            text_to_speech=self.text_to_speech,
            session_id="test-session",
        )

    def test_runs_complete_voice_turn(self) -> None:
        question = (
            "Dove si trova il Martirio di sant'Orsola?"
        )
        response = BotResponse(
            text=(
                "Il Martirio di sant'Orsola si trova "
                "alle Gallerie d'Italia di Napoli."
            ),
            intent=Intent.ARTWORK_LOCATION,
        )

        self.speech_to_text.listen.return_value = question
        self.chatbot_service.process.return_value = response

        result = self.app.run_once()

        self.speech_to_text.listen.assert_called_once_with()
        self.chatbot_service.process.assert_called_once_with(
            session_id="test-session",
            text=question,
        )
        self.text_to_speech.speak.assert_called_once_with(
            response.text
        )
        self.assertIs(result, response)

    def test_uses_same_session_for_follow_up(self) -> None:
        first_response = BotResponse(
            text="Prima risposta.",
            intent=Intent.ARTWORK_LOCATION,
        )
        second_response = BotResponse(
            text="Seconda risposta.",
            intent=Intent.ARTWORK_DESCRIPTION,
        )

        self.speech_to_text.listen.side_effect = [
            "Dove si trova?",
            "Dimmi di più.",
        ]
        self.chatbot_service.process.side_effect = [
            first_response,
            second_response,
        ]

        self.app.run_once()
        self.app.run_once()

        self.assertEqual(
            self.chatbot_service.process.call_args_list[0].kwargs[
                "session_id"
            ],
            "test-session",
        )
        self.assertEqual(
            self.chatbot_service.process.call_args_list[1].kwargs[
                "session_id"
            ],
            "test-session",
        )

    def test_rejects_empty_session_id(self) -> None:
        with self.assertRaises(ValueError):
            VoiceChatbotApp(
                chatbot_service=self.chatbot_service,
                speech_to_text=self.speech_to_text,
                text_to_speech=self.text_to_speech,
                session_id="   ",
            )


if __name__ == "__main__":
    unittest.main()
