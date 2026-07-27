from dataclasses import dataclass, field
from datetime import datetime

from src.core.enums import (
    ClaimType,
    EntityType,
    InconsistencyType,
    Intent,
)


@dataclass
class Artist:
    uri: str
    name: str
    normalized_name: str
    full_name: str | None = None
    birth_date: str | None = None
    death_date: str | None = None
    birth_place: str | None = None
    death_place: str | None = None
    description: str | None = None
    image_url: str | None = None
    source: str = "DBpedia"


@dataclass
class Place:
    uri: str
    name: str
    normalized_name: str
    city: str
    place_type: str | None = None
    address: str | None = None
    latitude: float | None = None
    longitude: float | None = None
    description: str | None = None
    image_url: str | None = None
    source: str = "DBpedia"


@dataclass
class Artwork:
    uri: str
    title: str
    normalized_title: str
    artist_uri: str
    artist_name: str
    place_uri: str | None = None
    place_name: str | None = None
    city: str | None = None
    year: int | None = None
    completion_date: str | None = None
    medium: str | None = None
    subject: str | None = None
    description: str | None = None
    image_url: str | None = None
    source: str = "DBpedia"


@dataclass
class EntityMention:
    entity_type: EntityType
    text: str
    canonical_name: str | None = None
    uri: str | None = None
    confidence: float = 0.0
    start: int | None = None
    end: int | None = None


@dataclass
class Claim:
    claim_type: ClaimType
    subject_uri: str | None
    claimed_value: str
    confidence: float = 0.0


@dataclass
class NLUResult:
    raw_text: str
    normalized_text: str
    intent: Intent
    intent_confidence: float
    entities: list[EntityMention] = field(default_factory=list)
    claims: list[Claim] = field(default_factory=list)


@dataclass
class Inconsistency:
    inconsistency_type: InconsistencyType
    message: str
    claimed_value: str | None = None
    correct_value: str | None = None


@dataclass
class DialogueState:
    session_id: str
    turn_index: int = 0
    last_intent: Intent | None = None
    current_artist_uri: str | None = None
    current_artwork_uri: str | None = None
    current_place_uri: str | None = None
    last_result_uris: list[str] = field(default_factory=list)
    pending_clarification: str | None = None
    clarification_options: list[str] = field(default_factory=list)
    updated_at: datetime = field(default_factory=datetime.utcnow)


@dataclass
class ConversationTurn:
    session_id: str
    turn_index: int
    user_text: str
    assistant_text: str
    intent: Intent
    timestamp: datetime = field(default_factory=datetime.utcnow)
    entities: list[EntityMention] = field(default_factory=list)
    inconsistency: Inconsistency | None = None


@dataclass
class BotResponse:
    text: str
    intent: Intent
    artworks: list[Artwork] = field(default_factory=list)
    artists: list[Artist] = field(default_factory=list)
    places: list[Place] = field(default_factory=list)
    inconsistency: Inconsistency | None = None
    needs_clarification: bool = False
    clarification_options: list[str] = field(default_factory=list)
