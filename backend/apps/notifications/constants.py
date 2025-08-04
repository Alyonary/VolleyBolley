class NotificationTypes:
    '''Notification types constants.'''
    in_game: str = 'joinGame'
    rate: str = 'rate'
    removed: str = 'removed'

class Notification:
    '''
    Notification object with type, title, body, and screen.
    This class is used to create a notification object based on the type.
    
    '''
    def __init__(self, notification_type):
        params = self._get_params(notification_type)
        self.type = notification_type
        self.title = params['title']
        self.body = params['body']
        self.screen = params['screen']

    @staticmethod
    def _get_params(notification_type):
        templates = {
            NotificationTypes.in_game: {
                'title': 'Game Invitation',
                'body': 'You are invited to a game!',
                'screen': 'inGame',
            },
            NotificationTypes.rate: {
                'title': 'Rate the game',
                'body': 'Please rate the game!',
                'screen': 'rate',
            },
            NotificationTypes.removed: {
                'title': 'You have been removed from the game',
                'body': 'See details in the app',
                'screen': 'removed',
            },
        }
        if notification_type not in templates:
            raise ValueError('Unknown notification type')
        params = templates[notification_type].copy()
        return params

class FCMTokenAction:
    '''FCM token actions constants.'''
    UPDATE: str = 'update'
    SET: str = 'set'
    DEACTIVATE: str = 'deactivate'
    CHOICES: list[tuple[str]] = [
        (UPDATE, 'update'),
        (SET, 'set'),
        (DEACTIVATE, 'deactivate'),
    ]

class DeviceType:
    '''Device type choices constants.'''
    ANDROID = 'android'
    IOS = 'ios'
    CHOICES = [
        (ANDROID, 'android'),
        (IOS, 'ios'),
    ]

DEVICE_MAX_LENGTH: int = 255