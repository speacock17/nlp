class SpeechToTextCache:
    def __init__(
        self,
        factory,
        initial_engine_name: str | None = None,
        initial_engine=None,
    ) -> None:
        if not callable(factory):
            raise TypeError(
                "La factory STT deve essere invocabile"
            )

        self._factory = factory
        self._engines = {}

        if initial_engine is not None:
            normalized_name = self._normalize_name(
                initial_engine_name
            )
            self._engines[normalized_name] = (
                initial_engine
            )

    def get(self, engine_name: str):
        normalized_name = self._normalize_name(
            engine_name
        )

        if normalized_name not in self._engines:
            self._engines[normalized_name] = (
                self._factory(normalized_name)
            )

        return self._engines[normalized_name]

    @staticmethod
    def _normalize_name(
        engine_name: str | None,
    ) -> str:
        if not isinstance(engine_name, str):
            raise TypeError(
                "Il nome del motore STT deve essere "
                "una stringa"
            )

        normalized_name = (
            engine_name.strip().lower()
        )

        if not normalized_name:
            raise ValueError(
                "Il nome del motore STT non pu? "
                "essere vuoto"
            )

        return normalized_name
