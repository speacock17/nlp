from os import getenv
import customtkinter as ctk
from uuid import uuid4

from dotenv import load_dotenv

from src.database.neo4j_knowledge_repository import (
    Neo4jKnowledgeRepository,
)
from src.database.neo4j_memory_repository import (
    Neo4jMemoryRepository,
)
from src.dialogue.chatbot_service_factory import (
    create_chatbot_service,
)
from src.gui.chatbot_gui_controller import (
    ChatbotGuiController,
)
from src.gui.chatbot_window import ChatbotWindow
from src.gui.speech_to_text_cache import (
    SpeechToTextCache,
)
from src.speech.speech_to_text_factory import (
    create_speech_to_text,
)
from src.speech.text_to_speech import TextToSpeech


def main() -> None:
    knowledge_repository = None
    memory_repository = None

    try:
        load_dotenv()

        knowledge_repository = (
            Neo4jKnowledgeRepository.from_env()
        )
        memory_repository = (
            Neo4jMemoryRepository.from_env()
        )

        if not knowledge_repository.check_health():
            raise RuntimeError(
                "Il database Neo4j non ? raggiungibile"
            )

        chatbot_service = create_chatbot_service(
            knowledge_repository=knowledge_repository,
            memory_repository=memory_repository,
        )

        stt_engine = getenv(
            "STT_ENGINE",
            "whisper",
        )

        speech_to_text = create_speech_to_text(
            stt_engine
        )
        text_to_speech = TextToSpeech()

        speech_to_text_cache = SpeechToTextCache(
            factory=create_speech_to_text,
            initial_engine_name=stt_engine,
            initial_engine=speech_to_text,
        )

        controller = ChatbotGuiController(
            chatbot_service=chatbot_service,
            speech_to_text=speech_to_text,
            text_to_speech=text_to_speech,
            session_id=str(uuid4()),
        )

        root = ctk.CTk()

        ChatbotWindow(
            root=root,
            controller=controller,
            speech_to_text_cache=(
                speech_to_text_cache
            ),
            default_engine=stt_engine,
        )

        root.mainloop()

    finally:
        if knowledge_repository is not None:
            knowledge_repository.close()

        if memory_repository is not None:
            memory_repository.close()


if __name__ == "__main__":
    main()

