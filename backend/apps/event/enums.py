from enum import Enum


class EventFieldLength(int, Enum):
    TITLE = 150
    STR_MAX_LEN = 50
    WORKING_HOURS = 100
    MESSAGE = 300
    PAYMENT_TYPE = 30
    PAYMENT_VALUE = 60
    EVENT_TIME = 20
