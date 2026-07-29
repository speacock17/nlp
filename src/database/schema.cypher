// ============================================================
// Vincoli di unicità: sottografo della conoscenza
// ============================================================

CREATE CONSTRAINT artist_uri_unique IF NOT EXISTS
FOR (artist:Artist)
REQUIRE artist.uri IS UNIQUE;

CREATE CONSTRAINT artwork_uri_unique IF NOT EXISTS
FOR (artwork:Artwork)
REQUIRE artwork.uri IS UNIQUE;

CREATE CONSTRAINT place_uri_unique IF NOT EXISTS
FOR (place:Place)
REQUIRE place.uri IS UNIQUE;


// ============================================================
// Vincoli di unicità: sottografo della memoria
// ============================================================

CREATE CONSTRAINT session_id_unique IF NOT EXISTS
FOR (session:Session)
REQUIRE session.session_id IS UNIQUE;

CREATE CONSTRAINT conversation_turn_identity_unique IF NOT EXISTS
FOR (turn:ConversationTurn)
REQUIRE (turn.session_id, turn.turn_index) IS UNIQUE;


// ============================================================
// Indici per le operazioni richieste da KnowledgeRepository
// ============================================================

CREATE INDEX artist_normalized_name_index IF NOT EXISTS
FOR (artist:Artist)
ON (artist.normalized_name);

CREATE INDEX artwork_normalized_title_index IF NOT EXISTS
FOR (artwork:Artwork)
ON (artwork.normalized_title);

CREATE INDEX artwork_city_index IF NOT EXISTS
FOR (artwork:Artwork)
ON (artwork.city);

CREATE INDEX place_normalized_name_index IF NOT EXISTS
FOR (place:Place)
ON (place.normalized_name);

CREATE INDEX place_city_index IF NOT EXISTS
FOR (place:Place)
ON (place.city);


// ============================================================
// Indici per le operazioni richieste da MemoryRepository
// ============================================================

CREATE INDEX session_updated_at_index IF NOT EXISTS
FOR (session:Session)
ON (session.updated_at);

CREATE INDEX conversation_turn_timestamp_index IF NOT EXISTS
FOR (turn:ConversationTurn)
ON (turn.timestamp);
