from io import BytesIO

import speech_recognition as sr
from faster_whisper import WhisperModel

from src.speech.exceptions import (
    SpeechInputTimeoutError,
    SpeechNotUnderstoodError,
    SpeechRecognitionServiceError,
)


DEFAULT_INITIAL_PROMPT = (
    "Caravaggio, Michelangelo Merisi, "
    "Battistello Caracciolo, Napoli, "
    "Martirio di sant'Orsola, "
    "Sette opere di Misericordia, "
    "Flagellazione di Cristo"
)


class WhisperSpeechToText:
    def __init__(
        self,
        model=None,
        recognizer: sr.Recognizer | None = None,
        microphone_factory=None,
        language: str = "it",
        pause_threshold: float = 1.5,
        model_name: str = "small",
        device: str = "cpu",
        compute_type: str = "int8",
        initial_prompt: str = DEFAULT_INITIAL_PROMPT,
    ) -> None:
        if not isinstance(pause_threshold, (int, float)):
            raise TypeError(
                "pause_threshold deve essere numerico"
            )

        if pause_threshold <= 0:
            raise ValueError(
                "pause_threshold deve essere maggiore di zero"
            )

        if not isinstance(language, str) or not language.strip():
            raise ValueError(
                "La lingua Whisper non pu\u00f2 essere vuota"
            )

        self._recognizer = recognizer or sr.Recognizer()
        self._microphone_factory = (
            microphone_factory or sr.Microphone
        )
        self._language = language.strip()
        self._initial_prompt = initial_prompt
        self._model = (
            model
            if model is not None
            else WhisperModel(
                model_name,
                device=device,
                compute_type=compute_type,
            )
        )

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

            wav_data = audio.get_wav_data()

            with BytesIO(wav_data) as audio_stream:
                segments, _ = self._model.transcribe(
                    audio_stream,
                    language=self._language,
                    vad_filter=True,
                    initial_prompt=self._initial_prompt,
                    condition_on_previous_text=False,
                )

                transcription = "".join(
                    segment.text
                    for segment in segments
                ).strip()

        except sr.WaitTimeoutError as error:
            raise SpeechInputTimeoutError(
                "Nessun parlato rilevato entro il timeout"
            ) from error

        except (
            SpeechInputTimeoutError,
            SpeechNotUnderstoodError,
        ):
            raise

        except Exception as error:
            raise SpeechRecognitionServiceError(
                "Il motore Whisper non \u00e8 disponibile"
            ) from error

        if not transcription:
            raise SpeechNotUnderstoodError(
                "Whisper non ha prodotto una trascrizione"
            )

        return transcription
