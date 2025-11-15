from enum import Enum


class LocationEnums(int, Enum):
    LOCATION_NAME_LENGTH = 100
    MIN_LATITUDE = -90
    MAX_LATITUDE = 90
    MIN_LONGTITUDE = -180
    MAX_LONGTITUDE = 180


class CourtEnums(int, Enum):
    WORKING_HOURS_LENGTH = 255
