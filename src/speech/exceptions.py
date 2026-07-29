class SpeechError(Exception):
    """Errore base del sottosistema vocale."""


class SpeechInputTimeoutError(SpeechError):
    """Nessun parlato rilevato entro il timeout."""


class SpeechNotUnderstoodError(SpeechError):
    """L'audio non può essere trascritto."""


class SpeechRecognitionServiceError(SpeechError):
    """Il servizio STT non è disponibile."""
