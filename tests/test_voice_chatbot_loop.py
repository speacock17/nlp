import unittest
from unittest.mock import MagicMock, call

from src.app import VoiceChatbotApp
from src.core.enums import Intent
from src.core.models import BotResponse
from src.speech.exceptions import (
    SpeechInputTimeoutError,
    SpeechNotUnderstoodError,
    SpeechRecognitionServiceError,
)


class VoiceChatbotLoopTest(unittest.TestCase):
    def setUp(self) -> None:
        self.chatbot_service = MagicMock()
        self.speech_to_text = MagicMock()
        self.text_to_speech = MagicMock()
        self.output_writer = MagicMock()

        self.app = VoiceChatbotApp(
            chatbot_service=self.chatbot_service,
            speech_to_text=self.speech_to_text,
            text_to_speech=self.text_to_speech,
            session_id="voice-session",
            output_writer=self.output_writer,
        )

    def test_runs_until_user_says_exit(self) -> None:
        response = BotResponse(
            text=(
                "Il Martirio di sant'Orsola si trova "
                "presso Palazzo Zevallos."
            ),
            intent=Intent.ARTWORK_LOCATION,
        )

        self.speech_to_text.listen.side_effect = [
            "Dove si trova il Martirio di sant'Orsola?",
            "esci",
        ]
        self.chatbot_service.process.return_value = response

        self.app.run()

        self.chatbot_service.process.assert_called_once_with(
            session_id="voice-session",
            text=(
                "Dove si trova il Martirio "
                "di sant'Orsola?"
            ),
        )
        self.text_to_speech.speak.assert_has_calls(
            [
                call(response.text),
                call("Arrivederci."),
            ]
        )

    def test_continues_after_input_timeout(self) -> None:
        self.speech_to_text.listen.side_effect = [
            SpeechInputTimeoutError(),
            "esci",
        ]

        self.app.run()

        self.chatbot_service.process.assert_not_called()
        self.output_writer.assert_any_call(
            "Non ho rilevato alcuna domanda."
        )

    def test_continues_after_unrecognized_audio(
        self,
    ) -> None:
        self.speech_to_text.listen.side_effect = [
            SpeechNotUnderstoodError(),
            "esci",
        ]

        self.app.run()

        self.chatbot_service.process.assert_not_called()
        self.output_writer.assert_any_call(
            "Non ho compreso l'audio. Riprova."
        )

    def test_stops_after_recognition_service_error(
        self,
    ) -> None:
        self.speech_to_text.listen.side_effect = (
            SpeechRecognitionServiceError()
        )

        self.app.run()

        self.chatbot_service.process.assert_not_called()
        self.output_writer.assert_any_call(
            "Il servizio di riconoscimento vocale "
            "non è disponibile."
        )


if __name__ == "__main__":
    unittest.main()
