class PushServiceMessages:
    """Messages used in Push Service responses."""

    NO_DEVICES_FOUND: str = 'No devices found for player'
    NOTIFICATION_TYPE_NOT_FOUND: str = 'Notification type not found'
    NO_DEVICES_FOR_EVENT: str = 'Not found any devices to send message'
    ALL_NOT_DELIVERED: str = 'All notifications failed'
    EMPTY_TOKEN: str = 'Empty device token, skipping notification'
    SUCCESS: str = 'Notification sent successfully'
    SERVICE_UNAVAILABLE: str = 'Push service unavailable'
    ANSWER_SAMPLE: dict[str, str | bool | int | None] = {
        'success': False,
        'total_devices': 0,
        'delivered': 0,
        'failed': 0,
        'message': '',
        'notification_type': None,
        'notifications_data': None,
    }


class InfrastructureLogMessages:
    """Logs for Redis, Celery, and connection inspectors."""

    CELERY_NO_WORKERS: str = 'No active Celery workers found'
    CELERY_NOT_READY: str = 'Celery not ready: {error}'
    UNKNOWN_ERROR: str = 'Unknown error: {error}'
    REDIS_DNS_ERROR: str = (
        'DNS Error: Host {host} not found. Check docker-compose '
        'or your hosts file.'
    )
    REDIS_UNKNOWN_ERROR: str = 'Unknown Redis error: {error}'
    TASK_WORKER_ERROR: str = 'Error connecting with workers: {error}'
    TASK_CREATED: str = 'Task successfully created.'
    TASK_ERROR: str = 'Error during create task: {error}'


class ConnectionLogMessages:
    """Logs for service availability checks and reconnection logic."""

    INIT_START: str = 'Initializing FCM and Celery services...'
    INIT_SUCCESS: str = (
        'Firebase and Celery services connected successfully, '
        'notifications enabled.'
    )
    INIT_FAILED: str = 'Error initializing services: {error}'
    INIT_UNEXPECTED_ERROR: str = (
        'Unexpected error during initialization: {error}'
    )
    RECONNECT_START: str = 'Attempting to reconnect services.'
    RECONNECT_SUCCESS: str = (
        'FCM and Celery workers are available. Notifications enabled.'
    )
    RECONNECT_FAILED: str = (
        'FCM and/or Celery workers are NOT available. Notifications disabled.'
    )
    SERVICE_MISSING: str = (
        'Service not available for {func}, attempting reconnection.'
    )
    SERVICE_SKIPPED: str = 'Service still unavailable, skipping {func}.'
    UNEXPECTED_ERROR: str = 'Unexpected error during {action}: {error}'

    FCM_ADMIN_OK: str = 'FB_admin initialized successfully.'
    FCM_FILE_CREATED: str = 'FCM file created at {path}'
    FCM_FAIL: str = 'FCM service not available\n'
    CELERY_FAIL: str = 'Celery workers not available'


class SenderLogMessages:
    """Logs for the actual process of sending push notifications."""

    PUSH_RESULTS: str = (
        'Push notification "{notif_type}" results: '
        '{delivered}/{total} successful, {failed} failed'
    )
    EMPTY_TOKEN: str = 'Device token is empty, skipping'
    SENDING_TO: str = 'Sending notification to device {token}'
    SEND_SUCCESS: str = 'Notification sent successfully to device {token}'
    FCM_SEND_ERROR: str = 'FCM Error sending to {token}: {error}'
    UNEXPECTED_SEND_ERROR: str = 'Unexpected error sending to {token}: {error}'
    RETRY_SCHEDULED: str = (
        'Scheduled retry task for token {token} in {time} seconds'
    )
    RETRY_FAILED: str = 'Failed to schedule retry task for {token}: {error}'


class RepositoryLogMessages:
    """Logs for database models and data integrity."""

    UNKNOWN_TYPE: str = 'Unknown notification type: {notif_type}'
    TYPE_NOT_FOUND: str = 'Notification type {notif_type} not found'
    DB_CREATED: str = 'Notification DB model created for player {player}'
    DB_CREATION_ERROR: str = (
        'Error creating notification DB model for player {player}: {error}'
    )
