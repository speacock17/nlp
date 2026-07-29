import pyttsx3


class TextToSpeech:
    def __init__(
        self,
        engine=None,
        rate: int = 170,
        volume: float = 1.0,
    ) -> None:
        if not isinstance(rate, int):
            raise TypeError(
                "La velocit? deve essere un numero intero"
            )

        if rate <= 0:
            raise ValueError(
                "La velocit? deve essere maggiore di zero"
            )

        if not isinstance(volume, (int, float)):
            raise TypeError(
                "Il volume deve essere numerico"
            )

        if not 0.0 <= volume <= 1.0:
            raise ValueError(
                "Il volume deve essere compreso tra 0 e 1"
            )

        self._engine = (
            engine
            if engine is not None
            else pyttsx3.init()
        )

        self._engine.setProperty(
            "rate",
            rate,
        )
        self._engine.setProperty(
            "volume",
            float(volume),
        )

    def speak(self, text: str) -> None:
        if not isinstance(text, str):
            raise TypeError(
                "Il testo da pronunciare deve essere una stringa"
            )

        clean_text = text.strip()

        if not clean_text:
            raise ValueError(
                "Il testo da pronunciare non pu? essere vuoto"
            )

        self._engine.say(clean_text)
        self._engine.runAndWait()
