from src.speech.speech_to_text import SpeechToText
from src.speech.whisper_speech_to_text import (
    WhisperSpeechToText,
)


def create_speech_to_text(engine_name: str | None = None):
    normalized_name = (
        "whisper"
        if engine_name is None
        else engine_name.strip().lower()
    )

    if normalized_name == "google":
        return SpeechToText()

    if normalized_name == "whisper":
        return WhisperSpeechToText()

    raise ValueError(
        "Motore STT non valido. "
        "Valori ammessi: google, whisper"
    )
