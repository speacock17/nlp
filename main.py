from os import getenv
from uuid import uuid4

from dotenv import load_dotenv

from src.app import VoiceChatbotApp
from src.database.neo4j_knowledge_repository import (
    Neo4jKnowledgeRepository,
)
from src.database.neo4j_memory_repository import (
    Neo4jMemoryRepository,
)
from src.dialogue.chatbot_service import ChatbotService
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
                "Il database Neo4j non e raggiungibile"
            )

        chatbot_service = ChatbotService(
            knowledge_repository=knowledge_repository,
            memory_repository=memory_repository,
        )

        stt_engine = getenv(
            "STT_ENGINE",
            "whisper",
        )

        app = VoiceChatbotApp(
            chatbot_service=chatbot_service,
            speech_to_text=create_speech_to_text(
                stt_engine
            ),
            text_to_speech=TextToSpeech(),
            session_id=str(uuid4()),
        )

        app.run()
    finally:
        if knowledge_repository is not None:
            knowledge_repository.close()

        if memory_repository is not None:
            memory_repository.close()


if __name__ == "__main__":
    main()
