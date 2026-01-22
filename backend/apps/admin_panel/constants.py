from enum import Enum

MAX_FILE_SIZE: int = 10 * 1024 * 1024  # 10 MB
SUPPORTED_FILE_TYPES: tuple[str] = ('json', 'excel')
MONTHS_STAT_PAGINATION: int = 12
SEND_TYPE_CHOICES = [
    ('send_to_player', ('send to player')),
    ('send_to_event', ('send to event')),
]


class SendType(Enum):
    SEND_TO_PLAYER = 'send_to_player'
    SEND_TO_EVENT = 'send_to_event'


class UploadServiceMessages:
    EXCEL_MISSING_MODEL_FIELDS = 'Missing fields in model attrs: '
    EXCEL_INVALID_MODEL_FIELDS = 'Invalid fields in model attrs: '
    FILE_TYPE_NOT_SUPPORTED = 'Unsupported file type: '
    RESTRICTED_UPLOAD = 'Restricted upload in production mode for model: '
    UNKNOWN_MODEL_MAPPING = 'Unknown model mapping for file: '
    NO_MODEL_SERIALIZER = 'No serializer for model:'
    SUCCESS_DOWNLOAD = '✅ File processed successfully.'
    ERROR_DOWNLOAD = '❌ File processing failed: '
    UNEXPECTED_ERROR = '❌ Unexpected error: '
    NO_DATA_IN_JSON = 'No data found in JSON file'

    FILE_SIZE_EXCEEDED = 'File size exceeded the maximum limit.'
    INVALID_JSON_FORMAT = 'Invalid JSON format.'
    INVALID_EXCEL_FORMAT = 'Invalid Excel format.'
    INVALID_MODEL_ATTRS = 'Invalid fields in model attrs.'
    DATA_VALIDATION_FAILED = 'Data validation failed.'
    DATA_PROCESSING_SUCCESS = 'Data processed successfully.'
