from enum import Enum

MAX_FILE_SIZE: int = 10 * 1024 * 1024  # 10 MB
SUPPORTED_FILE_TYPES: tuple[str] = ('json', 'excel')
SEND_TYPE_CHOICES = [
    ('send_to_player', ('send to player')),
    ('send_to_event', ('send to event')),
]


class SendType(Enum):
    SEND_TO_PLAYER = 'send_to_player'
    SEND_TO_EVENT = 'send_to_event'
