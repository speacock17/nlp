from collections.abc import Callable

from src.core.models import BotResponse
from src.nlp.preprocessing import preprocess_question
from src.speech.exceptions import (
    SpeechInputTimeoutError,
    SpeechNotUnderstoodError,
    SpeechRecognitionServiceError,
)


class VoiceChatbotApp:
    def __init__(
        self,
        chatbot_service,
        speech_to_text,
        text_to_speech,
        session_id: str,
        output_writer: Callable[[str], None] = print,
    ) -> None:
        if not isinstance(session_id, str):
            raise TypeError(
                "L'identificativo di sessione deve essere una stringa"
            )

        clean_session_id = session_id.strip()

        if not clean_session_id:
            raise ValueError(
                "L'identificativo di sessione non pu? essere vuoto"
            )

        if not callable(output_writer):
            raise TypeError(
                "Il gestore dell'output deve essere invocabile"
            )

        self._chatbot_service = chatbot_service
        self._speech_to_text = speech_to_text
        self._text_to_speech = text_to_speech
        self._session_id = clean_session_id
        self._output_writer = output_writer

    def run_once(self) -> BotResponse:
        user_text = self._speech_to_text.listen()

        response = self._chatbot_service.process(
            session_id=self._session_id,
            text=user_text,
        )

        self._text_to_speech.speak(response.text)

        return response

    def run(self) -> None:
        self._output_writer(
            "Chatbot vocale avviato. "
            "Pronuncia 'esci' per terminare."
        )

        while True:
            try:
                self._output_writer("In ascolto...")
                user_text = self._speech_to_text.listen()

            except SpeechInputTimeoutError:
                self._output_writer(
                    "Non ho rilevato alcuna domanda."
                )
                continue

            except SpeechNotUnderstoodError:
                self._output_writer(
                    "Non ho compreso l'audio. Riprova."
                )
                continue

            except SpeechRecognitionServiceError:
                self._output_writer(
                    "Il servizio di riconoscimento vocale "
                    "non è disponibile."
                )
                return

            except KeyboardInterrupt:
                self._say_goodbye()
                return

            self._output_writer(
                f"Utente: {user_text}"
            )

            if self._is_exit_command(user_text):
                self._say_goodbye()
                return

            response = self._chatbot_service.process(
                session_id=self._session_id,
                text=user_text,
            )

            self._output_writer(
                f"Chatbot: {response.text}"
            )
            self._text_to_speech.speak(
                response.text
            )

    @staticmethod
    def _is_exit_command(text: str) -> bool:
        normalized_text = preprocess_question(text)

        return normalized_text in {
            "esci",
            "termina",
            "chiudi",
            "arrivederci",
        }

    def _say_goodbye(self) -> None:
        goodbye = "Arrivederci."
        self._output_writer(
            f"Chatbot: {goodbye}"
        )
        self._text_to_speech.speak(goodbye)
