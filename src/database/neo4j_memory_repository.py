import json
import os
from datetime import datetime
from typing import Any

from dotenv import load_dotenv
from neo4j import Driver, GraphDatabase, ManagedTransaction

from src.core.enums import EntityType, InconsistencyType, Intent
from src.core.interfaces import MemoryRepository
from src.core.models import (
    ConversationTurn,
    DialogueState,
    EntityMention,
    Inconsistency,
)


class Neo4jMemoryRepository(MemoryRepository):
    def __init__(
        self,
        uri: str,
        user: str,
        password: str,
        database: str = "neo4j",
    ) -> None:
        self._driver = GraphDatabase.driver(
            uri,
            auth=(user, password),
        )
        self._database = database

    @classmethod
    def from_env(cls) -> "Neo4jMemoryRepository":
        load_dotenv()

        uri = os.getenv("NEO4J_URI")
        user = os.getenv("NEO4J_USER")
        password = os.getenv("NEO4J_PASSWORD")
        database = os.getenv("NEO4J_DATABASE", "neo4j")

        missing = [
            name
            for name, value in (
                ("NEO4J_URI", uri),
                ("NEO4J_USER", user),
                ("NEO4J_PASSWORD", password),
            )
            if not value
        ]

        if missing:
            raise RuntimeError(
                "Variabili d'ambiente mancanti: "
                + ", ".join(missing)
            )

        return cls(
            uri=uri,
            user=user,
            password=password,
            database=database,
        )

    def close(self) -> None:
        self._driver.close()

    def __enter__(self) -> "Neo4jMemoryRepository":
        return self

    def __exit__(
        self,
        exception_type: type[BaseException] | None,
        exception: BaseException | None,
        traceback: Any,
    ) -> None:
        self.close()

    @staticmethod
    def _validate_limit(limit: int) -> None:
        if limit <= 0:
            raise ValueError(
                "Il limite deve essere maggiore di zero"
            )

    @staticmethod
    def _serialize_entity(
        entity: EntityMention,
    ) -> dict[str, Any]:
        return {
            "entity_type": entity.entity_type.value,
            "text": entity.text,
            "canonical_name": entity.canonical_name,
            "uri": entity.uri,
            "confidence": entity.confidence,
            "start": entity.start,
            "end": entity.end,
        }

    @staticmethod
    def _deserialize_entity(
        data: dict[str, Any],
    ) -> EntityMention:
        return EntityMention(
            entity_type=EntityType(data["entity_type"]),
            text=data["text"],
            canonical_name=data.get("canonical_name"),
            uri=data.get("uri"),
            confidence=float(data.get("confidence", 0.0)),
            start=data.get("start"),
            end=data.get("end"),
        )

    @staticmethod
    def _serialize_inconsistency(
        inconsistency: Inconsistency | None,
    ) -> str | None:
        if inconsistency is None:
            return None

        return json.dumps(
            {
                "inconsistency_type":
                    inconsistency.inconsistency_type.value,
                "message": inconsistency.message,
                "claimed_value": inconsistency.claimed_value,
                "correct_value": inconsistency.correct_value,
            },
            ensure_ascii=False,
        )

    @staticmethod
    def _deserialize_inconsistency(
        value: str | None,
    ) -> Inconsistency | None:
        if value is None:
            return None

        data = json.loads(value)

        return Inconsistency(
            inconsistency_type=InconsistencyType(
                data["inconsistency_type"]
            ),
            message=data["message"],
            claimed_value=data.get("claimed_value"),
            correct_value=data.get("correct_value"),
        )

    @classmethod
    def _serialize_entities(
        cls,
        entities: list[EntityMention],
    ) -> str:
        return json.dumps(
            [
                cls._serialize_entity(entity)
                for entity in entities
            ],
            ensure_ascii=False,
        )

    @classmethod
    def _deserialize_entities(
        cls,
        value: str | None,
    ) -> list[EntityMention]:
        if value is None:
            return []

        data = json.loads(value)

        return [
            cls._deserialize_entity(item)
            for item in data
        ]

    @staticmethod
    def _state_properties(
        state: DialogueState,
    ) -> dict[str, Any]:
        properties: dict[str, Any] = {
            "session_id": state.session_id,
            "turn_index": state.turn_index,
            "last_result_uris": state.last_result_uris,
            "clarification_options":
                state.clarification_options,
            "updated_at": state.updated_at.isoformat(),
        }

        optional_properties = {
            "last_intent": (
                state.last_intent.value
                if state.last_intent is not None
                else None
            ),
            "current_artist_uri":
                state.current_artist_uri,
            "current_artwork_uri":
                state.current_artwork_uri,
            "current_place_uri":
                state.current_place_uri,
            "pending_clarification":
                state.pending_clarification,
        }

        properties.update(
            {
                key: value
                for key, value in optional_properties.items()
                if value is not None
            }
        )

        return properties

    @staticmethod
    def _to_state(
        properties: dict[str, Any],
    ) -> DialogueState:
        last_intent_value = properties.get("last_intent")

        return DialogueState(
            session_id=properties["session_id"],
            turn_index=int(
                properties.get("turn_index", 0)
            ),
            last_intent=(
                Intent(last_intent_value)
                if last_intent_value is not None
                else None
            ),
            current_artist_uri=properties.get(
                "current_artist_uri"
            ),
            current_artwork_uri=properties.get(
                "current_artwork_uri"
            ),
            current_place_uri=properties.get(
                "current_place_uri"
            ),
            last_result_uris=list(
                properties.get("last_result_uris", [])
            ),
            pending_clarification=properties.get(
                "pending_clarification"
            ),
            clarification_options=list(
                properties.get(
                    "clarification_options",
                    [],
                )
            ),
            updated_at=datetime.fromisoformat(
                properties["updated_at"]
            ),
        )

    @classmethod
    def _to_turn(
        cls,
        properties: dict[str, Any],
    ) -> ConversationTurn:
        return ConversationTurn(
            session_id=properties["session_id"],
            turn_index=int(properties["turn_index"]),
            user_text=properties["user_text"],
            assistant_text=properties["assistant_text"],
            intent=Intent(properties["intent"]),
            timestamp=datetime.fromisoformat(
                properties["timestamp"]
            ),
            entities=cls._deserialize_entities(
                properties.get("entities_json")
            ),
            inconsistency=cls._deserialize_inconsistency(
                properties.get("inconsistency_json")
            ),
        )

    def create_session(
        self,
        session_id: str,
    ) -> DialogueState:
        existing = self.load_state(session_id)

        if existing is not None:
            return existing

        state = DialogueState(session_id=session_id)
        self.save_state(state)

        return state

    def load_state(
        self,
        session_id: str,
    ) -> DialogueState | None:
        records, _, _ = self._driver.execute_query(
            """
            MATCH (session:Session {
                session_id: $session_id
            })
            RETURN session
            LIMIT 1
            """,
            session_id=session_id,
            database_=self._database,
        )

        if not records:
            return None

        return self._to_state(
            dict(records[0]["session"])
        )

    def save_state(
        self,
        state: DialogueState,
    ) -> None:
        properties = self._state_properties(state)

        self._driver.execute_query(
            """
            MERGE (session:Session {
                session_id: $session_id
            })
            SET session = $properties
            """,
            session_id=state.session_id,
            properties=properties,
            database_=self._database,
        )

    @staticmethod
    def _write_turn(
        transaction: ManagedTransaction,
        turn_properties: dict[str, Any],
        session_defaults: dict[str, Any],
    ) -> None:
        transaction.run(
            """
            MERGE (session:Session {
                session_id: $session_id
            })
            ON CREATE SET session = $session_defaults

            MERGE (turn:ConversationTurn {
                session_id: $session_id,
                turn_index: $turn_index
            })
            SET turn = $turn_properties

            MERGE (session)-[:HAS_TURN]->(turn)
            """,
            session_id=turn_properties["session_id"],
            turn_index=turn_properties["turn_index"],
            turn_properties=turn_properties,
            session_defaults=session_defaults,
        ).consume()

    def save_turn(
        self,
        turn: ConversationTurn,
    ) -> None:
        turn_properties: dict[str, Any] = {
            "session_id": turn.session_id,
            "turn_index": turn.turn_index,
            "user_text": turn.user_text,
            "assistant_text": turn.assistant_text,
            "intent": turn.intent.value,
            "timestamp": turn.timestamp.isoformat(),
            "entities_json": self._serialize_entities(
                turn.entities
            ),
        }

        inconsistency_json = (
            self._serialize_inconsistency(
                turn.inconsistency
            )
        )

        if inconsistency_json is not None:
            turn_properties[
                "inconsistency_json"
            ] = inconsistency_json

        session_defaults = self._state_properties(
            DialogueState(
                session_id=turn.session_id,
                updated_at=turn.timestamp,
            )
        )

        with self._driver.session(
            database=self._database
        ) as session:
            session.execute_write(
                self._write_turn,
                turn_properties,
                session_defaults,
            )

    def get_recent_turns(
        self,
        session_id: str,
        limit: int = 10,
    ) -> list[ConversationTurn]:
        self._validate_limit(limit)

        records, _, _ = self._driver.execute_query(
            """
            MATCH (:Session {
                session_id: $session_id
            })-[:HAS_TURN]->(turn:ConversationTurn)
            RETURN turn
            ORDER BY turn.turn_index DESC
            LIMIT $limit
            """,
            session_id=session_id,
            limit=limit,
            database_=self._database,
        )

        turns = [
            self._to_turn(dict(record["turn"]))
            for record in records
        ]

        turns.reverse()

        return turns

    @staticmethod
    def _clear_session_transaction(
        transaction: ManagedTransaction,
        session_id: str,
    ) -> None:
        transaction.run(
            """
            MATCH (turn:ConversationTurn {
                session_id: $session_id
            })
            DETACH DELETE turn
            """,
            session_id=session_id,
        ).consume()

        transaction.run(
            """
            MATCH (session:Session {
                session_id: $session_id
            })
            DETACH DELETE session
            """,
            session_id=session_id,
        ).consume()

    def clear_session(
        self,
        session_id: str,
    ) -> None:
        with self._driver.session(
            database=self._database
        ) as session:
            session.execute_write(
                self._clear_session_transaction,
                session_id,
            )
