from pyfcm import FCMNotification

from apps.notifications.constants import Notification, NotificationTypes
from apps.notifications.models import Device
from volleybolley.settings import FCM_API_KEY

push_service = FCMNotification(api_key=FCM_API_KEY)


def send_notifications(
    type: str,
    player_id: int | None = None,
    game_id: int | None = None
) -> bool:
    '''
    Sends a notification to multiple devices using FCM.

    Args:
        tokens (list): List of device tokens to send the notification to.
        type (str): Type of notification to send.
        game_id (int, optional): Game ID to include in the notification data.
    '''
    notification = Notification(type)
    if type == NotificationTypes.in_game:
        tokens = Device.objects.active(
            ).in_game(game_id).values_list('token', flat=True)
        if not tokens:
            return
        send_push_notification(
            tokens,
            notification,
            game_id=game_id
        )
        return
    elif type == NotificationTypes.rate:
        tokens = Device.objects.active(
            ).in_game(game_id).values_list('token', flat=True)
        if not tokens:
            return
        send_push_notification(
            tokens,
            notification,
            game_id=game_id
        )
        return
    elif type == NotificationTypes.removed:
        tokens = Device.objects.active(
            ).in_game(game_id).values_list('token', flat=True)
        if not tokens:
            return
        send_push_notification(
            tokens,
            notification,
            game_id=game_id
        )
        return

def send_push_notification(
    tokens: list[int],
    notification: Notification,
    game_id: int | None = None
) ->bool:
    '''
    Sends a push notification to multiple devices.

    Args:
        tokens (list): List of device tokens to send the notification to.
        notification (Notification): Notification object containing title,
            body, and screen.
        game_id (int, optional): Game ID to include in the notification data.
    '''
    data_message = {'screen': notification.screen}
    if game_id:
        data_message['gameId'] = game_id
    push_service.notify_multiple_devices(
        registration_ids=tokens,
        message_title=notification.title,
        message_body=notification.body,
        data_message={'screen': notification.screen, 'gameId': game_id}
        )
