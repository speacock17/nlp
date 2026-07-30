from src.core.models import BotResponse


class ChatbotGuiController:
    def __init__(
        self,
        chatbot_service,
        speech_to_text,
        text_to_speech,
        session_id: str,
    ) -> None:
        if not isinstance(session_id, str):
            raise TypeError(
                "L'identificativo di sessione deve essere "
                "una stringa"
            )

        clean_session_id = session_id.strip()

        if not clean_session_id:
            raise ValueError(
                "L'identificativo di sessione non pu? "
                "essere vuoto"
            )

        self._chatbot_service = chatbot_service
        self._speech_to_text = speech_to_text
        self._text_to_speech = text_to_speech
        self._session_id = clean_session_id

    def submit_text(
        self,
        text: str,
        speak_response: bool = True,
    ) -> BotResponse:
        if not isinstance(text, str):
            raise TypeError(
                "La domanda deve essere una stringa"
            )

        if not isinstance(speak_response, bool):
            raise TypeError(
                "speak_response deve essere booleano"
            )

        clean_text = text.strip()

        if not clean_text:
            raise ValueError(
                "La domanda non pu? essere vuota"
            )

        response = self._chatbot_service.process(
            session_id=self._session_id,
            text=clean_text,
        )

        if speak_response:
            self.speak_response(response)

        return response

    def speak_response(
        self,
        response: BotResponse,
    ) -> None:
        self._text_to_speech.speak(
            response.text
        )

    def listen_and_submit(
        self,
        speak_response: bool = True,
    ) -> tuple[str, BotResponse]:
        transcription = (
            self._speech_to_text.listen()
        )

        response = self.submit_text(
            transcription,
            speak_response=speak_response,
        )

        return transcription, response

    def set_speech_to_text(
        self,
        speech_to_text,
    ) -> None:
        if speech_to_text is None:
            raise ValueError(
                "Il motore STT non pu? essere nullo"
            )

        self._speech_to_text = speech_to_text
