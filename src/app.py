from src.core.models import BotResponse


class VoiceChatbotApp:
    def __init__(
        self,
        chatbot_service,
        speech_to_text,
        text_to_speech,
        session_id: str,
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

        self._chatbot_service = chatbot_service
        self._speech_to_text = speech_to_text
        self._text_to_speech = text_to_speech
        self._session_id = clean_session_id

    def run_once(self) -> BotResponse:
        user_text = self._speech_to_text.listen()

        response = self._chatbot_service.process(
            session_id=self._session_id,
            text=user_text,
        )

        self._text_to_speech.speak(response.text)

        return response
