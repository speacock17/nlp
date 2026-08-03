import speech_recognition as sr

from src.speech.exceptions import (
    SpeechInputTimeoutError,
    SpeechNotUnderstoodError,
    SpeechRecognitionServiceError,
)


class SpeechToText:
    def __init__(
        self,
        recognizer: sr.Recognizer | None = None,
        microphone_factory=None,
        language: str = "it-IT",
        pause_threshold: float = 1.5,
    ) -> None:
        if not isinstance(pause_threshold, (int, float)):
            raise TypeError(
                "pause_threshold deve essere numerico"
            )

        if pause_threshold <= 0:
            raise ValueError(
                "pause_threshold deve essere maggiore di zero"
            )

        self._recognizer = recognizer or sr.Recognizer()
        self._microphone_factory = (
            microphone_factory or sr.Microphone
        )
        self._language = language

        self._recognizer.pause_threshold = float(
            pause_threshold
        )

    def listen(
        self,
        timeout: float = 5.0,
        phrase_time_limit: float = 15.0,
    ) -> str:
        if timeout <= 0:
            raise ValueError(
                "Il timeout deve essere maggiore di zero"
            )

        if phrase_time_limit <= 0:
            raise ValueError(
                "Il limite della frase deve essere "
                "maggiore di zero"
            )

        try:
            with self._microphone_factory() as source:
                self._recognizer.adjust_for_ambient_noise(
                    source,
                    duration=0.5,
                )

                audio = self._recognizer.listen(
                    source,
                    timeout=timeout,
                    phrase_time_limit=phrase_time_limit,
                )

            transcription = (
                self._recognizer.recognize_google(
                    audio,
                    language=self._language,
                )
            )

        except sr.WaitTimeoutError as error:
            raise SpeechInputTimeoutError(
                "Nessun parlato rilevato entro il timeout"
            ) from error

        except sr.UnknownValueError as error:
            raise SpeechNotUnderstoodError(
                "Non è stato possibile comprendere l'audio"
            ) from error

        except sr.RequestError as error:
            raise SpeechRecognitionServiceError(
                "Il servizio di riconoscimento vocale "
                "non è disponibile"
            ) from error

        transcription = transcription.strip()

        if not transcription:
            raise SpeechNotUnderstoodError(
                "La trascrizione ottenuta è vuota"
            )

        return transcription
