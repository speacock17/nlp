import json
from dataclasses import dataclass, field
from typing import Any

from src.llm.ollama_llm_client import (
    LLMResponse,
    LLMToolCall,
)


SYSTEM_PROMPT = """
Sei un assistente dedicato esclusivamente alle opere di
Caravaggio e Battistello Caracciolo visitabili a Napoli.

Devi comprendere richieste formulate liberamente e scegliere
uno o pi? tool quando servono informazioni fattuali.

Regole obbligatorie:
- il database interrogato dai tool ? l'unica fonte di verit?;
- non inventare artisti, opere, luoghi, date o descrizioni;
- non usare conoscenze esterne;
- puoi chiamare soltanto i tool forniti;
- usa pi? tool quando la domanda contiene pi? richieste;
- se la domanda ? fuori dominio, rispondi brevemente spiegando
  il dominio supportato;
- se manca un'informazione essenziale, chiedi chiarimento;
- rispondi in italiano con una formulazione naturale e adatta
  alla sintesi vocale.
""".strip()


FINAL_ANSWER_PROMPT = """
Formula la risposta finale alla domanda dell'utente usando
esclusivamente i risultati dei tool riportati sotto.

Non aggiungere informazioni che non compaiono nei risultati.
Se un risultato indica che il dato non ? stato trovato,
dichiaralo chiaramente oppure chiedi un chiarimento.
Unisci correttamente i risultati di pi? tool in una sola
risposta naturale, breve e adatta alla sintesi vocale.
""".strip()


@dataclass(frozen=True)
class ToolExecution:
    tool_call: LLMToolCall
    result: dict[str, Any]


@dataclass(frozen=True)
class AgentResult:
    content: str
    executions: list[ToolExecution] = field(
        default_factory=list
    )


class ToolCallingAgent:
    def __init__(
        self,
        llm_client,
        tool_executor,
        tool_schemas: list[dict[str, Any]],
        max_tool_calls: int = 4,
    ) -> None:
        if not isinstance(max_tool_calls, int):
            raise TypeError(
                "max_tool_calls deve essere un intero"
            )

        if max_tool_calls <= 0:
            raise ValueError(
                "max_tool_calls deve essere maggiore di zero"
            )

        self._llm_client = llm_client
        self._tool_executor = tool_executor
        self._tool_schemas = tool_schemas
        self._max_tool_calls = max_tool_calls

    def run(
        self,
        user_text: str,
    ) -> AgentResult:
        if not isinstance(user_text, str):
            raise TypeError(
                "La richiesta dell'utente deve essere "
                "una stringa"
            )

        clean_text = user_text.strip()

        if not clean_text:
            raise ValueError(
                "La richiesta dell'utente non pu? "
                "essere vuota"
            )

        initial_response = self._llm_client.chat(
            messages=[
                {
                    "role": "system",
                    "content": SYSTEM_PROMPT,
                },
                {
                    "role": "user",
                    "content": clean_text,
                },
            ],
            tools=self._tool_schemas,
        )

        if not initial_response.tool_calls:
            return AgentResult(
                content=self._require_content(
                    initial_response
                ),
                executions=[],
            )

        if (
            len(initial_response.tool_calls)
            > self._max_tool_calls
        ):
            raise RuntimeError(
                "Il modello ha richiesto troppi tool"
            )

        executions = [
            self._execute_tool(tool_call)
            for tool_call in initial_response.tool_calls
        ]

        final_response = self._llm_client.chat(
            messages=[
                {
                    "role": "system",
                    "content": SYSTEM_PROMPT,
                },
                {
                    "role": "user",
                    "content": clean_text,
                },
                {
                    "role": "user",
                    "content": self._build_results_message(
                        executions
                    ),
                },
            ],
            tools=None,
        )

        return AgentResult(
            content=self._require_content(
                final_response
            ),
            executions=executions,
        )

    def _execute_tool(
        self,
        tool_call: LLMToolCall,
    ) -> ToolExecution:
        result = self._tool_executor.execute(
            name=tool_call.name,
            arguments=tool_call.arguments,
        )

        return ToolExecution(
            tool_call=tool_call,
            result=result,
        )

    @staticmethod
    def _build_results_message(
        executions: list[ToolExecution],
    ) -> str:
        payload = [
            {
                "tool": execution.tool_call.name,
                "arguments": (
                    execution.tool_call.arguments
                ),
                "result": execution.result,
            }
            for execution in executions
        ]

        return (
            f"{FINAL_ANSWER_PROMPT}\n\n"
            "RISULTATI DEI TOOL:\n"
            + json.dumps(
                payload,
                ensure_ascii=False,
                indent=2,
            )
        )

    @staticmethod
    def _require_content(
        response: LLMResponse,
    ) -> str:
        content = response.content.strip()

        if not content:
            raise RuntimeError(
                "Il modello non ha prodotto una risposta"
            )

        return content
