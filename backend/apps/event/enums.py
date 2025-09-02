from enum import IntEnum


class EventIntEnums(IntEnum):
    """Event app constants."""

    TITLE = 150
    STR_MAX_LEN = 50
    MESSAGE = 300
    PAYMENT_VALUE = 60
    ADMIN_LIST_PER_PAGE = 25

    MIN_PLAYERS = 4
    MAX_PLAYERS = 24
    MAX_TEAMS = 24
    MIN_TEAMS = 3
