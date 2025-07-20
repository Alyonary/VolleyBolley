from enum import Enum


class CoreFieldLength(int, Enum):
    """Константы для приложения Core."""

    NAME = 70
    NAME_STR = 30
    TITLE = 50
    TITLE_STR = 30
    CONTACT_NAME = 255
    ADMIN_LIST_PER_PAGE = 25
    ADMIN_INFO_SHORT_CONTENT = 50
