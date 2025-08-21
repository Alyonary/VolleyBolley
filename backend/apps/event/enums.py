from enum import Enum


class EventFieldLength(int, Enum):
    """Константы для приложения Event."""

    TITLE = 150
    STR_MAX_LEN = 50
    MESSAGE = 300
    PAYMENT_VALUE = 60
    ADMIN_LIST_PER_PAGE = 25


class NumberOfPlayers(int, Enum):
    """Max and min number of players in Event."""

    MIN_PLAYERS = 4
    MAX_PLAYERS = 24
    MAX_TEAMS = 24
    MIN_TEAMS = 3
