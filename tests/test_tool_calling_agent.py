import unittest
from unittest.mock import MagicMock, call

from src.llm.knowledge_tools import (
    KNOWLEDGE_TOOL_SCHEMAS,
)
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
        self.answer_renderer = MagicMock()
        self.tool_schemas = KNOWLEDGE_TOOL_SCHEMAS

        self.agent = ToolCallingAgent(
            llm_client=self.llm_client,
            tool_executor=self.tool_executor,
            tool_schemas=self.tool_schemas,
            answer_renderer=self.answer_renderer,
        )

    def test_executes_tool_and_renders_grounded_answer(
        self,
    ) -> None:
        self.llm_client.chat.return_value = LLMResponse(
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
        )

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
        self.answer_renderer.render.return_value = (
            "A Napoli puoi vedere tre opere "
            "di Caravaggio."
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
        self.answer_renderer.render.assert_called_once_with(
            result.executions
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
            self.llm_client.chat.call_count,
            1,
        )

    def test_executes_multiple_tools(self) -> None:
        self.llm_client.chat.return_value = LLMResponse(
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
        )

        self.tool_executor.execute.side_effect = [
            {"found": True, "data": {"year": 1607}},
            {
                "found": True,
                "data": {
                    "name": "Caravaggio"
                },
            },
        ]
        self.answer_renderer.render.return_value = (
            "Risposta combinata."
        )

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
        self.assertEqual(
            self.llm_client.chat.call_count,
            1,
        )

    def test_recovers_tool_call_from_json_content(
        self,
    ) -> None:
        self.llm_client.chat.return_value = LLMResponse(
            content=(
                '{"name":"list_artworks_by_artist",'
                '"parameters":{'
                '"artist_name":"Caravaggio",'
                '"city":"Napoli"}}'
            ),
            tool_calls=[],
        )
        self.tool_executor.execute.return_value = {
            "count": 1,
            "data": [
                {
                    "title": (
                        "Sette opere di Misericordia"
                    )
                }
            ],
        }
        self.answer_renderer.render.return_value = (
            "Nel database risulta un'opera."
        )

        result = self.agent.run(
            "Vorrei vedere qualche quadro del Merisi."
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
            "Nel database risulta un'opera.",
        )
        self.assertEqual(
            len(result.executions),
            1,
        )

    def test_normalizes_tool_call_before_execution(
        self,
    ) -> None:
        self.llm_client.chat.return_value = LLMResponse(
            content="",
            tool_calls=[
                LLMToolCall(
                    name="list_artworks_by_artist",
                    arguments={
                        "artist_name": "Merisi",
                        "city": "Napoli",
                    },
                )
            ],
        )
        self.tool_executor.execute.return_value = {
            "count": 1,
            "data": [
                {
                    "title": (
                        "Sette opere di Misericordia"
                    )
                }
            ],
        }
        self.answer_renderer.render.return_value = (
            "Nel database risulta un'opera."
        )

        result = self.agent.run(
            "Vorrei vedere qualche quadro "
            "del Merisi a Napoli."
        )

        self.tool_executor.execute.assert_called_once_with(
            name="list_artworks_by_artist",
            arguments={
                "artist_name": "Caravaggio",
                "city": "Napoli",
            },
        )
        self.assertEqual(
            result.executions[0].tool_call.arguments[
                "artist_name"
            ],
            "Caravaggio",
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
        self.answer_renderer.render.assert_not_called()

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
