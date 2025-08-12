


class NotificationTypes:
    '''Notification types constants.'''
    IN_GAME: str = 'joinGame'
    RATE: str = 'rate'
    REMOVED: str = 'removed'
    CHOICES = (
        (IN_GAME, IN_GAME),
        (RATE, RATE),
        (REMOVED, REMOVED),
    )

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
        '''Get notification parameters based on the type.'''
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
            raise ValueError('Unknown notification type')
        params = templates[notification_type].copy()
        return params


DEVICE_TOKEN_MAX_LENGTH: int = 255