import unittest
from unittest.mock import MagicMock

from src.llm.naturalizing_answer_renderer import (
    NaturalizingAnswerRenderer,
)
from src.llm.ollama_llm_client import (
    LLMResponse,
    LLMToolCall,
)
from src.llm.tool_calling_agent import ToolExecution


class NaturalizingAnswerRendererTest(unittest.TestCase):
    def setUp(self) -> None:
        self.llm_client = MagicMock()
        self.base_renderer = MagicMock()
        self.renderer = NaturalizingAnswerRenderer(
            llm_client=self.llm_client,
            base_renderer=self.base_renderer,
        )

    @staticmethod
    def _execution(
        tool_name: str = "list_artworks_by_artist",
        arguments=None,
    ) -> ToolExecution:
        return ToolExecution(
            tool_call=LLMToolCall(
                name=tool_name,
                arguments=arguments or {},
            ),
            result={"found": True},
        )

    def test_naturalizes_grounded_answer(self) -> None:
        executions = [self._execution()]
        self.base_renderer.render.return_value = (
            "Risposta deterministica verificata."
        )
        self.llm_client.chat.return_value = LLMResponse(
            content="Risposta più naturale."
        )

        result = self.renderer.render(executions)

        self.assertEqual(
            result,
            "Risposta più naturale.",
        )
        self.base_renderer.render.assert_called_once_with(
            executions
        )
        self.llm_client.chat.assert_called_once()

    def test_falls_back_when_llm_fails(self) -> None:
        executions = [self._execution()]
        self.base_renderer.render.return_value = (
            "Risposta deterministica."
        )
        self.llm_client.chat.side_effect = RuntimeError(
            "LLM non disponibile"
        )

        result = self.renderer.render(executions)

        self.assertEqual(
            result,
            "Risposta deterministica.",
        )

    def test_falls_back_when_llm_returns_empty(self) -> None:
        executions = [self._execution()]
        self.base_renderer.render.return_value = (
            "Risposta deterministica."
        )
        self.llm_client.chat.return_value = LLMResponse(
            content=""
        )

        result = self.renderer.render(executions)

        self.assertEqual(
            result,
            "Risposta deterministica.",
        )

    def test_description_bypasses_naturalization(
        self,
    ) -> None:
        executions = [
            self._execution(
                tool_name="get_artwork_information",
                arguments={
                    "requested_information": "description",
                },
            )
        ]
        self.base_renderer.render.return_value = (
            "Descrizione verbatim"
        )

        result = self.renderer.render(executions)

        self.assertEqual(
            result,
            "Descrizione verbatim",
        )
        self.llm_client.chat.assert_not_called()


    def test_description_with_other_information_is_naturalized(
        self,
    ) -> None:
        executions = [
            self._execution(
                tool_name="get_artwork_information",
                arguments={
                    "requested_information": "location",
                },
            ),
            self._execution(
                tool_name="get_artwork_information",
                arguments={
                    "requested_information": "date",
                },
            ),
            self._execution(
                tool_name="get_artwork_information",
                arguments={
                    "requested_information": "description",
                },
            ),
        ]

        self.base_renderer.render.return_value = (
            "Luogo. Data. Descrizione."
        )
        self.llm_client.chat.return_value = LLMResponse(
            content="Risposta combinata naturale."
        )

        result = self.renderer.render(executions)

        self.assertEqual(
            result,
            "Risposta combinata naturale.",
        )
        self.llm_client.chat.assert_called_once()


if __name__ == "__main__":
    unittest.main()
