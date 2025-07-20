from enum import Enum


class EventFieldLength(int, Enum):
    """Константы для приложения Event."""

    TITLE = 150
    STR_MAX_LEN = 30
    MESSAGE = 300
    PAYMENT_VALUE = 60
    ADMIN_LIST_PER_PAGE = 25
