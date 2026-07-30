import json
from dataclasses import dataclass, field
from typing import Any, Callable

from ollama import chat


@dataclass(frozen=True)
class LLMToolCall:
    name: str
    arguments: dict[str, Any] = field(
        default_factory=dict
    )


@dataclass(frozen=True)
class LLMResponse:
    content: str
    tool_calls: list[LLMToolCall] = field(
        default_factory=list
    )


class OllamaLLMClient:
    def __init__(
        self,
        model: str = "llama3.2:3b",
        chat_function: Callable[..., Any] = chat,
    ) -> None:
        if not isinstance(model, str):
            raise TypeError(
                "Il nome del modello deve essere "
                "una stringa"
            )

        clean_model = model.strip()

        if not clean_model:
            raise ValueError(
                "Il nome del modello non pu? essere "
                "vuoto"
            )

        if not callable(chat_function):
            raise TypeError(
                "La funzione chat deve essere invocabile"
            )

        self._model = clean_model
        self._chat_function = chat_function

    def chat(
        self,
        messages: list[dict[str, Any]],
        tools: list[dict[str, Any]] | None = None,
    ) -> LLMResponse:
        response = self._chat_function(
            model=self._model,
            messages=messages,
            tools=tools,
        )

        message = response.message
        content = (message.content or "").strip()
        raw_tool_calls = message.tool_calls or []

        tool_calls = [
            self._convert_tool_call(tool_call)
            for tool_call in raw_tool_calls
        ]

        return LLMResponse(
            content=content,
            tool_calls=tool_calls,
        )

    @staticmethod
    def _convert_tool_call(
        tool_call: Any,
    ) -> LLMToolCall:
        function = tool_call.function
        arguments = function.arguments or {}

        if isinstance(arguments, str):
            arguments = json.loads(arguments)

        if not isinstance(arguments, dict):
            raise TypeError(
                "Gli argomenti del tool devono essere "
                "un dizionario"
            )

        return LLMToolCall(
            name=function.name,
            arguments=arguments,
        )
