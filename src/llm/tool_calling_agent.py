import json
from dataclasses import dataclass, field
from typing import Any

from src.llm.domain_tool_call_normalizer import (
    DomainToolCallNormalizer,
)
from src.llm.ollama_llm_client import (
    LLMResponse,
    LLMToolCall,
)


SYSTEM_PROMPT = """
Sei il componente di comprensione linguistica di un chatbot
dedicato esclusivamente alle opere di Caravaggio e Battistello
Caracciolo visitabili a Napoli.

Il tuo compito ? soltanto interpretare la richiesta e scegliere
uno o pi? tool quando servono informazioni fattuali.

Regole obbligatorie:
- il database interrogato dai tool ? l'unica fonte di verit?;
- non rispondere usando conoscenze esterne;
- non inventare artisti, opere, luoghi, date o descrizioni;
- puoi chiamare soltanto i tool forniti;
- usa pi? tool se la domanda contiene pi? richieste;
- Michelangelo Merisi, Merisi e Caravaggio indicano lo stesso
  artista: usa sempre il nome Caravaggio negli argomenti;
- il dominio riguarda Caravaggio, Battistello Caracciolo e le
  loro opere visitabili nell'area urbana di Napoli;
- se la domanda ? fuori dominio, rispondi brevemente indicando
  il dominio supportato;
- se manca un'informazione essenziale, chiedi un chiarimento;
- quando ? necessario interrogare il database, restituisci una
  chiamata tool strutturata e non una risposta fattuale libera.
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
        answer_renderer=None,
        tool_call_normalizer=None,
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

        if answer_renderer is None:
            from src.llm.grounded_answer_renderer import (
                GroundedAnswerRenderer,
            )

            answer_renderer = GroundedAnswerRenderer()

        self._llm_client = llm_client
        self._tool_executor = tool_executor
        self._tool_schemas = tool_schemas
        self._answer_renderer = answer_renderer
        self._tool_call_normalizer = (
            tool_call_normalizer
            if tool_call_normalizer is not None
            else DomainToolCallNormalizer()
        )
        self._max_tool_calls = max_tool_calls
        self._allowed_tool_names = (
            self._extract_allowed_tool_names(
                tool_schemas
            )
        )

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

        response = self._llm_client.chat(
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

        tool_calls = list(response.tool_calls)

        if not tool_calls:
            tool_calls = self._tool_calls_from_content(
                response.content
            )

        if not tool_calls:
            return AgentResult(
                content=self._require_content(response),
                executions=[],
            )

        if len(tool_calls) > self._max_tool_calls:
            raise RuntimeError(
                "Il modello ha richiesto troppi tool"
            )

        normalized_tool_calls = [
            self._tool_call_normalizer.normalize(
                user_text=clean_text,
                tool_call=tool_call,
            )
            for tool_call in tool_calls
        ]

        executions = [
            self._execute_tool(tool_call)
            for tool_call in normalized_tool_calls
        ]

        grounded_content = self._answer_renderer.render(
            executions
        )

        if not grounded_content.strip():
            raise RuntimeError(
                "Il renderer non ha prodotto una risposta"
            )

        return AgentResult(
            content=grounded_content.strip(),
            executions=executions,
        )

    def _execute_tool(
        self,
        tool_call: LLMToolCall,
    ) -> ToolExecution:
        if tool_call.name not in self._allowed_tool_names:
            raise ValueError(
                f"Tool non autorizzato: {tool_call.name}"
            )

        result = self._tool_executor.execute(
            name=tool_call.name,
            arguments=tool_call.arguments,
        )

        return ToolExecution(
            tool_call=tool_call,
            result=result,
        )

    def _tool_calls_from_content(
        self,
        content: str,
    ) -> list[LLMToolCall]:
        clean_content = content.strip()

        if not clean_content:
            return []

        try:
            payload = self._load_json_with_repairs(
                clean_content
            )
        except json.JSONDecodeError:
            return []

        raw_calls = (
            payload
            if isinstance(payload, list)
            else [payload]
        )

        tool_calls = []

        for raw_call in raw_calls:
            if not isinstance(raw_call, dict):
                return []

            function_data = raw_call.get(
                "function",
                raw_call,
            )

            if not isinstance(function_data, dict):
                return []

            name = function_data.get("name")
            arguments = function_data.get(
                "arguments",
                function_data.get("parameters", {}),
            )

            if (
                not isinstance(name, str)
                or name not in self._allowed_tool_names
            ):
                return []

            if isinstance(arguments, str):
                try:
                    arguments = self._load_json_with_repairs(
                        arguments
                    )
                except json.JSONDecodeError as error:
                    raise RuntimeError(
                        "Gli argomenti JSON del tool "
                        "non sono validi"
                    ) from error

            if not isinstance(arguments, dict):
                raise TypeError(
                    "Gli argomenti del tool devono essere "
                    "un dizionario"
                )

            tool_calls.append(
                LLMToolCall(
                    name=name,
                    arguments=arguments,
                )
            )

        return tool_calls

    @staticmethod
    def _load_json_with_repairs(
        content: str,
    ) -> Any:
        try:
            return json.loads(content)
        except json.JSONDecodeError as original_error:
            repaired_content = content.replace(
                "\\'",
                "'",
            )

            if repaired_content == content:
                raise

            try:
                return json.loads(repaired_content)
            except json.JSONDecodeError:
                raise original_error

    @staticmethod
    def _extract_allowed_tool_names(
        tool_schemas: list[dict[str, Any]],
    ) -> set[str]:
        names = set()

        for schema in tool_schemas:
            function = schema.get("function", {})

            if not isinstance(function, dict):
                continue

            name = function.get("name")

            if isinstance(name, str) and name.strip():
                names.add(name.strip())

        return names

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
