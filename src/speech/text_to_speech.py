import pyttsx3


class TextToSpeech:
    def __init__(
        self,
        engine=None,
        engine_factory=None,
        rate: int = 170,
        volume: float = 1.0,
    ) -> None:
        if not isinstance(rate, int):
            raise TypeError(
                "La velocit\u00e0 deve essere un numero intero"
            )

        if rate <= 0:
            raise ValueError(
                "La velocit\u00e0 deve essere maggiore di zero"
            )

        if not isinstance(volume, (int, float)):
            raise TypeError(
                "Il volume deve essere numerico"
            )

        if not 0.0 <= volume <= 1.0:
            raise ValueError(
                "Il volume deve essere compreso tra 0 e 1"
            )

        if engine is not None and engine_factory is not None:
            raise ValueError(
                "Specificare engine oppure engine_factory, non entrambi"
            )

        if engine_factory is not None and not callable(
            engine_factory
        ):
            raise TypeError(
                "engine_factory deve essere chiamabile"
            )

        self._engine = engine
        self._engine_factory = (
            engine_factory
            if engine_factory is not None
            else pyttsx3.init
        )
        self._rate = rate
        self._volume = float(volume)

        if self._engine is not None:
            self._configure_engine(
                self._engine
            )

    def speak(self, text: str) -> None:
        if not isinstance(text, str):
            raise TypeError(
                "Il testo da pronunciare deve essere una stringa"
            )

        clean_text = text.strip()

        if not clean_text:
            raise ValueError(
                "Il testo da pronunciare non pu\u00f2 essere vuoto"
            )

        engine = (
            self._engine
            if self._engine is not None
            else self._engine_factory()
        )

        if self._engine is None:
            self._configure_engine(engine)

        engine.say(clean_text)
        engine.runAndWait()

    def _configure_engine(self, engine) -> None:
        engine.setProperty(
            "rate",
            self._rate,
        )
        engine.setProperty(
            "volume",
            self._volume,
        )
