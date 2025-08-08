from pyfcm import FCMNotification
from pyfcm.errors import FCMError

from apps.notifications.constants import Notification, NotificationTypes
from apps.notifications.exceptions import FCMFileNotFoundError
from apps.notifications.models import Device
from volleybolley.settings import FCM_FILE_PATH

push_service = FCMNotification(
    service_account_file=FCM_FILE_PATH,
)

def check_fcm_file():
    '''
    Check if the FCM service account file exists.
    '''
    if not FCM_FILE_PATH.exists():
        raise FileNotFoundError(
            f"FCM service account file not found: {FCM_FILE_PATH}"
        )
    return True

def proccess_notifications_by_type(
    type: str,
    player_id: int | None = None,
    game_id: int | None = None
) -> None:
    '''
    Sends a notification to multiple devices using FCM.

    Args:
        tokens (list): List of device tokens to send the notification to.
        type (str): Type of notification to send.
        game_id (int, optional): Game ID to include in the notification data.
    '''
    check_fcm_file()
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
            ).by_player(player_id).values_list('token', flat=True)
        if not tokens:
            return
        send_push_notification(
            tokens,
            notification,
        )
        return

def send_push_notification(
    tokens: list[int],
    notification: Notification,
    game_id: int | None = None,
    push_service: FCMNotification = push_service
) -> None:
    '''
    Sends a push notification to multiple devices.

    Args:
        tokens (list): List of device tokens to send the notification to.
        notification (Notification): Notification object containing title,
            body, and screen.
        game_id (int, optional): Game ID to include in the notification data.
    '''
    try:
        check_fcm_file()
        #Перенести логику проверки fcm файла в воркфлоу?? (перед запуском бэка)
        data_message = {'screen': notification.screen}
        if game_id:
            data_message['gameId'] = game_id
        for token in tokens:
            try:
                push_service.notify(
                fcm_token=token,
                notification_title=notification.title,
                notification_body=notification.body,
                data_payload=data_message
                )
            except FCMError:
                continue
             # логировать ошибку, если нужно. переход к след. токену
        return True
    except FileNotFoundError as e:
        raise FCMFileNotFoundError() from e
    