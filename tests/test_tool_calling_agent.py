import unittest
from unittest.mock import MagicMock, call

from src.llm.ollama_llm_client import (
    LLMResponse,
    LLMToolCall,
)
from src.llm.tool_calling_agent import (
    ToolCallingAgent,
)


class ToolCallingAgentTest(unittest.TestCase):
    def setUp(self) -> None:
        self.llm_client = MagicMock()
        self.tool_executor = MagicMock()
        self.tool_schemas = [
            {
                "type": "function",
                "function": {
                    "name": "list_artworks_by_artist"
                },
            }
        ]

        self.agent = ToolCallingAgent(
            llm_client=self.llm_client,
            tool_executor=self.tool_executor,
            tool_schemas=self.tool_schemas,
        )

    def test_executes_tool_and_generates_final_answer(
        self,
    ) -> None:
        self.llm_client.chat.side_effect = [
            LLMResponse(
                content="",
                tool_calls=[
                    LLMToolCall(
                        name="list_artworks_by_artist",
                        arguments={
                            "artist_name": "Caravaggio",
                            "city": "Napoli",
                        },
                    )
                ],
            ),
            LLMResponse(
                content=(
                    "A Napoli puoi vedere tre opere "
                    "di Caravaggio."
                ),
                tool_calls=[],
            ),
        ]

        tool_result = {
            "count": 3,
            "data": [
                {"title": "Opera 1"},
                {"title": "Opera 2"},
                {"title": "Opera 3"},
            ],
        }
        self.tool_executor.execute.return_value = (
            tool_result
        )

        result = self.agent.run(
            "Voglio vedere quadri di Caravaggio "
            "a Napoli, quali sono?"
        )

        self.tool_executor.execute.assert_called_once_with(
            name="list_artworks_by_artist",
            arguments={
                "artist_name": "Caravaggio",
                "city": "Napoli",
            },
        )
        self.assertEqual(
            result.content,
            (
                "A Napoli puoi vedere tre opere "
                "di Caravaggio."
            ),
        )
        self.assertEqual(
            len(result.executions),
            1,
        )
        self.assertEqual(
            result.executions[0].result,
            tool_result,
        )

    def test_executes_multiple_tools(self) -> None:
        self.llm_client.chat.side_effect = [
            LLMResponse(
                content="",
                tool_calls=[
                    LLMToolCall(
                        name="get_artwork_information",
                        arguments={
                            "artwork_title": "Flagellazione"
                        },
                    ),
                    LLMToolCall(
                        name="get_artist_information",
                        arguments={
                            "artist_name": "Caravaggio"
                        },
                    ),
                ],
            ),
            LLMResponse(
                content="Risposta combinata.",
                tool_calls=[],
            ),
        ]

        self.tool_executor.execute.side_effect = [
            {"found": True, "data": {"year": 1607}},
            {
                "found": True,
                "data": {
                    "name": "Caravaggio"
                },
            },
        ]

        result = self.agent.run(
            "Quando fu realizzata la Flagellazione "
            "e parlami di Caravaggio?"
        )

        self.assertEqual(
            self.tool_executor.execute.call_args_list,
            [
                call(
                    name="get_artwork_information",
                    arguments={
                        "artwork_title": "Flagellazione"
                    },
                ),
                call(
                    name="get_artist_information",
                    arguments={
                        "artist_name": "Caravaggio"
                    },
                ),
            ],
        )
        self.assertEqual(
            len(result.executions),
            2,
        )
        self.assertEqual(
            result.content,
            "Risposta combinata.",
        )

    def test_returns_direct_non_tool_response(self) -> None:
        self.llm_client.chat.return_value = LLMResponse(
            content=(
                "Posso rispondere soltanto sulle opere "
                "di Caravaggio e Battistello a Napoli."
            ),
            tool_calls=[],
        )

        result = self.agent.run(
            "Che tempo fa oggi?"
        )

        self.assertEqual(
            result.content,
            (
                "Posso rispondere soltanto sulle opere "
                "di Caravaggio e Battistello a Napoli."
            ),
        )
        self.assertEqual(
            result.executions,
            [],
        )
        self.tool_executor.execute.assert_not_called()

    def test_rejects_too_many_tool_calls(self) -> None:
        self.llm_client.chat.return_value = LLMResponse(
            content="",
            tool_calls=[
                LLMToolCall(
                    name="search_artworks",
                    arguments={"query": str(index)},
                )
                for index in range(5)
            ],
        )

        with self.assertRaises(RuntimeError):
            self.agent.run("Domanda troppo complessa")

        self.tool_executor.execute.assert_not_called()

    def test_rejects_empty_user_text(self) -> None:
        with self.assertRaises(ValueError):
            self.agent.run("   ")


if __name__ == "__main__":
    unittest.main()
