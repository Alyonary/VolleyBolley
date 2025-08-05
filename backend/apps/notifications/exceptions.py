class FCMFileNotFoundError(Exception):
    """Exception raised when the FCM service account file is not found."""
    pass

class FCMSendMessageError(Exception):
    """Exception raised when there is an error sending a message via FCM."""
    pass