class UploadError(Exception):
    """Base exception for upload service errors"""

    def __init__(self, message):
        self.message = message
        super().__init__(self.message)


class RestrictedFileError(UploadError):
    """Raised when the file is marked as private/restricted"""

    pass


class UnknownMappingError(UploadError):
    """Raised when no model mapping exists for the filename"""

    pass


class MissingSerializerError(UploadError):
    """Raised when the mapping class lacks a serializer defined"""

    pass


class ExcelValidationError(UploadError):
    """Raised when excel headers don't match expected fields"""

    pass
