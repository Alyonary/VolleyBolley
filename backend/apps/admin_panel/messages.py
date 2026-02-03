class UploadServiceMessages:
    """
    Storage for service-level notification and error messages.

    Contains standardized string constants used for logging and
    returning feedback during the file upload and processing lifecycle.
    """

    EXCEL_MISSING_MODEL_FIELDS: str = 'Missing fields in model attrs: '
    EXCEL_INVALID_MODEL_FIELDS: str = 'Invalid fields in model attrs: '
    FILE_TYPE_NOT_SUPPORTED: str = 'Unsupported file type: '
    RESTRICTED_UPLOAD: str = 'Restricted upload in production mode for model: '
    UNKNOWN_MODEL_MAPPING: str = 'Unknown model mapping for file: '
    NO_MODEL_SERIALIZER: str = 'No serializer for model:'
    SUCCESS_DOWNLOAD: str = '✅ File processed successfully.'
    ERROR_DOWNLOAD: str = '❌ File processing failed: '
    UNEXPECTED_ERROR: str = '❌ Unexpected error: '
    NO_DATA_IN_JSON: str = 'No data found in JSON file'
