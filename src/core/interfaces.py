from abc import ABC, abstractmethod

from src.core.models import (
    Artist,
    Artwork,
    ConversationTurn,
    DialogueState,
    Place,
)


class KnowledgeRepository(ABC):
    @abstractmethod
    def check_health(self) -> bool:
        raise NotImplementedError

    @abstractmethod
    def get_artwork_by_uri(self, artwork_uri: str) -> Artwork | None:
        raise NotImplementedError

    @abstractmethod
    def get_artwork_by_title(self, artwork_title: str) -> Artwork | None:
        raise NotImplementedError

    @abstractmethod
    def search_artworks(
        self,
        query: str,
        limit: int = 5,
    ) -> list[Artwork]:
        raise NotImplementedError

    @abstractmethod
    def list_artworks_by_artist(
        self,
        artist_name: str,
        city: str = "Napoli",
    ) -> list[Artwork]:
        raise NotImplementedError

    @abstractmethod
    def list_artworks_by_place(
        self,
        place_name: str,
    ) -> list[Artwork]:
        raise NotImplementedError

    @abstractmethod
    def get_artist_by_name(self, artist_name: str) -> Artist | None:
        raise NotImplementedError

    @abstractmethod
    def get_artist_by_uri(self, artist_uri: str) -> Artist | None:
        raise NotImplementedError

    @abstractmethod
    def search_artists(
        self,
        query: str,
        limit: int = 5,
    ) -> list[Artist]:
        raise NotImplementedError

    @abstractmethod
    def list_places(self) -> list[Place]:
        raise NotImplementedError

    @abstractmethod
    def get_place_by_name(self, place_name: str) -> Place | None:
        raise NotImplementedError

    @abstractmethod
    def search_places(
        self,
        query: str,
        limit: int = 5,
    ) -> list[Place]:
        raise NotImplementedError


class MemoryRepository(ABC):
    @abstractmethod
    def create_session(self, session_id: str) -> DialogueState:
        raise NotImplementedError

    @abstractmethod
    def load_state(self, session_id: str) -> DialogueState | None:
        raise NotImplementedError

    @abstractmethod
    def save_state(self, state: DialogueState) -> None:
        raise NotImplementedError

    @abstractmethod
    def save_turn(self, turn: ConversationTurn) -> None:
        raise NotImplementedError

    @abstractmethod
    def get_recent_turns(
        self,
        session_id: str,
        limit: int = 10,
    ) -> list[ConversationTurn]:
        raise NotImplementedError

    @abstractmethod
    def clear_session(self, session_id: str) -> None:
        raise NotImplementedError
