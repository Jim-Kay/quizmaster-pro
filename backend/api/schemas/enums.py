from enum import Enum

class CognitiveLevelEnum(str, Enum):
    """Enum for cognitive levels in Bloom's Taxonomy."""
    REMEMBER = "REMEMBER"
    UNDERSTAND = "UNDERSTAND"
    APPLY = "APPLY"
    ANALYZE = "ANALYZE"
    EVALUATE = "EVALUATE"
    CREATE = "CREATE"
