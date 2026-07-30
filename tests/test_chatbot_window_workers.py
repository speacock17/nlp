import unittest
from unittest.mock import MagicMock

from src.gui.chatbot_window import ChatbotWindow


class ChatbotWindowWorkerTest(unittest.TestCase):
    def setUp(self) -> None:
        self.window = ChatbotWindow.__new__(
            ChatbotWindow
        )
        self.window._controller = MagicMock()
        self.window._events = MagicMock()
        self.window._speech_to_text_cache = (
            MagicMock()
        )

        self.response = MagicMock()
        self.response.text = "Risposta immediata."

    def test_text_is_displayed_before_tts(
        self,
    ) -> None:
        operations = []

        self.window._controller.submit_text.return_value = (
            self.response
        )
        self.window._events.put.side_effect = (
            lambda event: operations.append(
                ("event", event)
            )
        )
        self.window._controller.speak_response.side_effect = (
            lambda response: operations.append(
                ("speak", response)
            )
        )

        self.window._process_text(
            "Domanda testuale"
        )

        self.window._controller.submit_text.assert_called_once_with(
            "Domanda testuale",
            speak_response=False,
        )
        self.assertEqual(
            operations[0],
            (
                "event",
                (
                    "response",
                    "Risposta immediata.",
                ),
            ),
        )
        self.assertEqual(
            operations[1],
            (
                "speak",
                self.response,
            ),
        )
        self.assertEqual(
            operations[2],
            (
                "event",
                ("speech_done",),
            ),
        )

    def test_voice_messages_are_displayed_before_tts(
        self,
    ) -> None:
        operations = []
        speech_to_text = MagicMock()

        self.window._speech_to_text_cache.get.return_value = (
            speech_to_text
        )
        self.window._controller.listen_and_submit.return_value = (
            "Domanda vocale",
            self.response,
        )
        self.window._events.put.side_effect = (
            lambda event: operations.append(
                ("event", event)
            )
        )
        self.window._controller.speak_response.side_effect = (
            lambda response: operations.append(
                ("speak", response)
            )
        )

        self.window._process_voice("whisper")

        self.window._controller.listen_and_submit.assert_called_once_with(
            speak_response=False,
        )
        self.assertEqual(
            operations[0],
            (
                "event",
                (
                    "voice_response",
                    "Domanda vocale",
                    "Risposta immediata.",
                ),
            ),
        )
        self.assertEqual(
            operations[1],
            (
                "speak",
                self.response,
            ),
        )
        self.assertEqual(
            operations[2],
            (
                "event",
                ("speech_done",),
            ),
        )


if __name__ == "__main__":
    unittest.main()
