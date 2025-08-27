from typing import TypeAlias


class NotificationTypes:
    """Notification types constants."""
    IN_GAME: str = 'joinGame'
    RATE: str = 'rate'
    REMOVED: str = 'removed'
    CHOICES = (IN_GAME, RATE, REMOVED)


class Notification:
    """
    Notification object with type, title, body, and screen.
    This class is used to create a notification object based on the type.
    """
    _instances = {}
    
    def __init__(self, notification_type):
        if hasattr(self, '_initialized'):
            return
        
        if not notification_type:
            raise ValueError('Notification type must be provided')
        
        if self.__class__ is Notification:
            raise TypeError(
                'Cannot instantiate Notification directly. '
                'Use Notification(notification_type) or subclasses.'
            )
        params = self._get_params(notification_type)
        self.type = notification_type
        self.title = params['title']
        self.body = params['body']
        self.screen = params['screen']
        
        self._initialized = True

    def __new__(cls, notification_type=None):
        if cls is Notification:
            if not notification_type:
                raise ValueError('Notification type must be provided')
            return cls._get_singleton_instance(notification_type)
        
        if cls not in cls._instances:
            cls._instances[cls] = super().__new__(cls)
        return cls._instances[cls]
    
    @classmethod
    def _get_singleton_instance(cls, notification_type):
        """Get singleton instance based on notification type."""
        if notification_type == NotificationTypes.IN_GAME:
            return InGameNotification(notification_type)
        elif notification_type == NotificationTypes.RATE:
            return RateNotification(notification_type)
        elif notification_type == NotificationTypes.REMOVED:
            return RemovedNotification(notification_type)
        else:
            raise ValueError(f'Unknown notification type: {notification_type}')
    
    @staticmethod
    def _get_params(notification_type):
        """Get notification parameters based on the type."""
        templates = {
            NotificationTypes.IN_GAME: {
                'title': 'Game Invitation',
                'body': 'You are invited to a game!',
                'screen': 'inGame',
            },
            NotificationTypes.RATE: {
                'title': 'Rate the game',
                'body': 'Please rate the game!',
                'screen': 'rate',
            },
            NotificationTypes.REMOVED: {
                'title': 'You have been removed from the game',
                'body': 'See details in the app.',
                'screen': 'removed',
            },
        }
        if notification_type not in templates:
            raise ValueError(f'Unknown notification type: {notification_type}')
        return templates[notification_type].copy()


class InGameNotification(Notification):
    """In-game notification singleton."""
    
    def __init__(self, notification_type=NotificationTypes.IN_GAME):
        super().__init__(notification_type)


class RateNotification(Notification):
    """Rate notification singleton."""
    
    def __init__(self, notification_type=NotificationTypes.RATE):
        super().__init__(notification_type)


class RemovedNotification(Notification):
    """Removed notification singleton."""
    
    def __init__(self, notification_type=NotificationTypes.REMOVED):
        super().__init__(notification_type)


NotificationsClass: TypeAlias = (
    Notification | InGameNotification | RateNotification | RemovedNotification
)