import unittest
from unittest.mock import MagicMock

from src.llm.ollama_llm_client import (
    LLMResponse,
    LLMToolCall,
    OllamaLLMClient,
)


class OllamaLLMClientTest(unittest.TestCase):
    def setUp(self) -> None:
        self.chat_function = MagicMock()
        self.client = OllamaLLMClient(
            model="llama3.2:3b",
            chat_function=self.chat_function,
        )

    def test_returns_text_response(self) -> None:
        response = MagicMock()
        response.message.content = (
            "Le opere disponibili sono tre."
        )
        response.message.tool_calls = None
        self.chat_function.return_value = response

        result = self.client.chat(
            messages=[
                {
                    "role": "user",
                    "content": "Quali opere posso vedere?",
                }
            ]
        )

        self.assertEqual(
            result,
            LLMResponse(
                content="Le opere disponibili sono tre.",
                tool_calls=[],
            ),
        )
        self.chat_function.assert_called_once_with(
            model="llama3.2:3b",
            messages=[
                {
                    "role": "user",
                    "content": "Quali opere posso vedere?",
                }
            ],
            tools=None,
        )

    def test_converts_tool_calls(self) -> None:
        tool_call = MagicMock()
        tool_call.function.name = (
            "list_artworks_by_artist"
        )
        tool_call.function.arguments = {
            "artist_name": "Caravaggio",
            "city": "Napoli",
        }

        response = MagicMock()
        response.message.content = ""
        response.message.tool_calls = [tool_call]
        self.chat_function.return_value = response

        result = self.client.chat(
            messages=[
                {
                    "role": "user",
                    "content": (
                        "Voglio vedere quadri di "
                        "Caravaggio a Napoli."
                    ),
                }
            ],
            tools=[
                {
                    "type": "function",
                    "function": {
                        "name": (
                            "list_artworks_by_artist"
                        )
                    },
                }
            ],
        )

        self.assertEqual(
            result.tool_calls,
            [
                LLMToolCall(
                    name="list_artworks_by_artist",
                    arguments={
                        "artist_name": "Caravaggio",
                        "city": "Napoli",
                    },
                )
            ],
        )

    def test_rejects_empty_model_name(self) -> None:
        with self.assertRaises(ValueError):
            OllamaLLMClient(
                model="   ",
                chat_function=self.chat_function,
            )


if __name__ == "__main__":
    unittest.main()
