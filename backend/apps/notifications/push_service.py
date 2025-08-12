from pyfcm import FCMNotification
from pyfcm.errors import FCMError

from apps.notifications.constants import Notification, NotificationTypes
from apps.notifications.exceptions import FCMFileNotFoundError, FCMServiceError
from apps.notifications.models import Device
from volleybolley.settings import FCM_FILE_PATH


def initialize_push_service():
    """
    Initialize the FCM service with the service account file.
    """
    #Перенести логику проверки fcm файла в воркфлоу?? (перед запуском бэка)
    try:
        check_fcm_file()
        fcm_file_path = FCM_FILE_PATH
        push_service = FCMNotification(
            service_account_file=fcm_file_path
        )
        return push_service
    except FCMError as e:
        raise FCMServiceError(
                "FCM service initialization failed. "
                "Check the service account file."
            ) from e


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
) -> bool | None:
    '''
    Sends a notification to multiple devices using FCM.

    Args:
        tokens (list): List of device tokens to send the notification to.
        type (str): Type of notification to send.
        game_id (int, optional): Game ID to include in the notification data.
    '''
    notification = Notification(type)
    if type == NotificationTypes.IN_GAME:
        tokens = Device.objects.active(
            ).in_game(game_id).values_list('token', flat=True)
        if not tokens:
            return 
        return send_push_notification(
            tokens,
            notification,
            game_id=game_id
        )
    elif type == NotificationTypes.RATE:
        tokens = Device.objects.active(
            ).in_game(game_id).values_list('token', flat=True)
        if not tokens:
            return
        return send_push_notification(
            tokens,
            notification,
            game_id=game_id
        )
    elif type == NotificationTypes.REMOVED:
        tokens = Device.objects.active(
            ).by_player(player_id).values_list('token', flat=True)
        if not tokens:
            return
        return send_push_notification(
            tokens,
            notification,
        )


push_service = initialize_push_service()


def send_push_notification(
    tokens: list[int],
    notification: Notification,
    game_id: int | None = None,
    push_service: FCMNotification = push_service
) -> bool | None:
    '''
    Sends a push notification to multiple devices.

    Args:
        tokens (list): List of device tokens to send the notification to.
        notification (Notification): Notification object containing title,
            body, and screen.
        game_id (int, optional): Game ID to include in the notification data.
    '''
    try:
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
        return True
    except FileNotFoundError as e:
        raise FCMFileNotFoundError() from e
    