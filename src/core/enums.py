from enum import Enum

class Intent(str, Enum):
    LIST_ARTWORKS_BY_ARTIST = "list_artworks_by_artist"
    ARTWORK_LOCATION = "artwork_location"
    ARTWORK_AUTHOR = "artwork_author"
    ARTWORK_DATE = "artwork_date"
    ARTWORK_DESCRIPTION = "artwork_description"
    ARTIST_INFO = "artist_info"
    LIST_PLACES = "list_places"
    PLACE_ARTWORKS = "place_artworks"
    COMPARE_ARTISTS = "compare_artists"
    FOLLOW_UP = "follow_up"
    OUT_OF_SCOPE = "out_of_scope"
    UNKNOWN = "unknown"


class EntityType(str, Enum):
    ARTIST = "artist"
    ARTWORK = "artwork"
    PLACE = "place"
    CITY = "city"
    DATE = "date"
    ORDINAL = "ordinal"


class ClaimType(str, Enum):
    ARTWORK_AUTHOR = "artwork_author"
    ARTWORK_LOCATION = "artwork_location"
    ARTWORK_DATE = "artwork_date"


class InconsistencyType(str, Enum):
    WRONG_AUTHOR = "wrong_author"
    WRONG_LOCATION = "wrong_location"
    IMPOSSIBLE_DATE = "impossible_date"
    ENTITY_NOT_FOUND = "entity_not_found"
    AMBIGUOUS_ENTITY = "ambiguous_entity"
