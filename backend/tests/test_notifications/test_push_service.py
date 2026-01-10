
import pytest
from pyfcm.errors import FCMError

from apps.event.models import Game
from apps.notifications.models import Device, Notifications, NotificationsBase
from apps.notifications.push_service import PushService


@pytest.mark.django_db
class TestPushServiceInitialization:
    """Test PushService initialization scenarios."""

    def test_successful_initialization_both_services_available(
        self, push_service_enabled: PushService
    ):
        """Test success initialization when FCM and Celery are available."""
        service: PushService = push_service_enabled
        assert service.connector.enable is True
        assert service.connector.celery_available is True
        assert service.connector._initialized is True
        assert hasattr(service.connector, 'push_service')

    def test_initialization_no_services_available(
        self, push_service_disabled: PushService
    ):
        """Test initialization when no services are available."""
        service: PushService = push_service_disabled
        assert service.connector.enable is False
        assert service.connector.celery_available is False
        assert service.connector._initialized is True

    def test_initialization_fcm_only_available(
        self, push_service_fcm_only: PushService
    ):
        """Test initialization when FCM is available but Celery is not."""
        service: PushService = push_service_fcm_only
        assert service.connector.enable is False
        assert service.connector.celery_available is False
        assert service.connector._initialized is True

    def test_initialization_with_fcm_error(
        self,
        monkeypatch,
        mock_fcm_service_fail,
    ):
        """Test initialization when FCM throws an error."""

        def mock_initialize_firebase(self):
            self.push_service = mock_fcm_service_fail
            return False

        def mock_check_celery_availability(self):
            return True

        monkeypatch.setattr(
            'apps.notifications.push_service.PushServiceConnector._initialize_firebase',
            mock_initialize_firebase,
        )
        monkeypatch.setattr(
            'apps.notifications.push_service.PushServiceConnector._check_celery_availability',
            mock_check_celery_availability,
        )

        service: PushService = PushService()
        assert service.connector.celery_available is True
        assert service.connector.enable is False
        assert service.connector._initialized is True


@pytest.mark.django_db
class TestPushServiceStatusMethods:
    """Test PushService status and checking methods."""

    def test_bool_method_all_services_available(
        self, push_service_enabled: PushService
    ):
        """Test __bool__ method when all services are available."""
        service: PushService = push_service_enabled
        assert service.connector.enable is True
        assert service.connector.celery_available is True
        assert service.connector._initialized is True
        assert bool(service.connector) is True

    def test_bool_method_services_unavailable(
        self, push_service_disabled: PushService
    ):
        """Test __bool__ method when services are unavailable."""
        service: PushService = push_service_disabled
        assert service.connector.enable is False
        assert service.connector.celery_available is False
        assert service.connector._initialized is True
        assert bool(service.connector) is False

    def test_get_status_returns_correct_dict(
        self, push_service_enabled: PushService
    ):
        """Test get_status returns correct status dictionary."""
        service: PushService = push_service_enabled
        status: dict = service.connector.get_status()

        expected_keys = {
            'notifications_enabled',
            'fcm_available',
            'celery_available',
            'initialized',
        }
        assert set(status.keys()) == expected_keys
        assert status['notifications_enabled'] is True
        assert status['fcm_available'] is True
        assert status['celery_available'] is True
        assert status['initialized'] is True

    def test_get_status_disabled_service(
        self, push_service_disabled: PushService
    ):
        """Test get_status for disabled service."""
        service: PushService = push_service_disabled
        status: dict = service.connector.get_status()

        assert status['notifications_enabled'] is False
        assert status['fcm_available'] is False
        assert status['celery_available'] is False
        assert status['initialized'] is True


@pytest.mark.django_db
class TestPushServiceNotificationMethods:
    """Test notification sending methods."""

    def test_send_notification_by_device_success(
        self,
        push_service_enabled: PushService,
        sample_notification: NotificationsBase,
        sample_device: Device,
    ):
        """Test successful single device notification."""
        service: PushService = push_service_enabled
        result: dict = service.sender.send_notification_by_device(
            sample_device,
            sample_notification,
        )
        assert result['success'] is True

    def test_send_notification_by_device_with_game_id(
        self,
        push_service_enabled: PushService,
        in_game_notification_type: NotificationsBase,
        sample_device: Device,
        game_for_notification: Game,
    ):
        """Test single device notification with game_id."""
        service: PushService = push_service_enabled
        assert game_for_notification is not None
        notif_in_db = Notifications.objects.filter(
            player=sample_device.player,
            game=game_for_notification,
        ).first()
        assert notif_in_db is None
        result: dict = service.send_to_device(
            player_id=sample_device.player.id,
            notification_type=in_game_notification_type.type,
            event_id=game_for_notification.id,
        )
        assert result['success'] is True
        notif_in_db = Notifications.objects.filter(
            player=sample_device.player,
            game=game_for_notification,
        ).first()
        assert notif_in_db is not None

    def test_send_notification_by_device_service_disabled(
        self,
        push_service_disabled: PushService,
        sample_notification: NotificationsBase,
        sample_device: Device,
    ):
        """Test notification when service is disabled."""
        service: PushService = push_service_disabled
        result: dict = service.send_to_device(
            sample_device,
            sample_notification,
        )
        assert result['success'] is False
        assert result['message'] == 'Push service is disabled.'

    def test_send_notification_by_device_fcm_error(
        self,
        push_service_enabled: PushService,
        mock_fcm_service_fail,
        sample_notification: NotificationsBase,
        mock_tasks_import,
        sample_device: Device,
    ):
        """Test notification with FCM error."""
        service: PushService = push_service_enabled
        # Patch notify method to raise FCMError
        service.connector.push_service.notify = mock_fcm_service_fail.notify
        result: dict = service.send_to_device(
            player_id=sample_device.player.id,
            notification_type=sample_notification.type,
            event_id=None,
        )
        assert result['success'] is False

    def test_send_push_notifications_multiple_devices(
        self,
        game_for_notification: Game,
        push_service_enabled: PushService,
        sample_notification: NotificationsBase,
        mock_fcm_service_fail,
        mock_tasks_import,
        devices: dict[str, list[Device]],
    ):
        """Test sending to multiple devices."""
        service: PushService = push_service_enabled
        devices_list: list[Device] = devices['active_devices']
        result: dict = service.sender.send_push_bulk(
            devices=devices_list,
            notification_type=sample_notification.type,
            event_id=game_for_notification.id,
        )
        assert isinstance(result, dict)
        assert result['total_devices'] == 3
        assert result['successful'] == 3
        assert result['failed'] == 0

        service.connector.push_service.notify = mock_fcm_service_fail.notify
        result_with_errors: dict = service.sender.send_push_bulk(
            devices=devices_list,
            notification_type=sample_notification.type,
            event_id=game_for_notification.id,
        )
        assert isinstance(result_with_errors, dict)
        assert result_with_errors['total_devices'] == 3
        assert result_with_errors['successful'] == 0
        assert result_with_errors['failed'] == 3

    def test_send_push_notifications_empty_tokens_list(
        self,
        push_service_enabled: PushService,
        sample_notification: NotificationsBase,
        game_for_notification: Game,
    ):
        """Test sending to empty devices list."""
        service: PushService = push_service_enabled
        devices: list[Device] = []
        result: dict = service.sender.send_push_bulk(
            devices=devices,
            notification_type=sample_notification.type,
            event_id=game_for_notification.id,
        )
        assert isinstance(result, dict)
        assert result['total_devices'] == 0
        assert result['successful'] == 0
        assert result['failed'] == 0


@pytest.mark.django_db
class TestPushServiceInternalMethods:
    """Test internal helper methods."""

    def test_send_notification_by_device_internal_success(
        self,
        push_service_enabled: PushService,
        sample_notification: NotificationsBase,
        sample_device: Device,
    ):
        """Test internal notification method success."""
        service: PushService = push_service_enabled
        result: bool = service.sender._send_notification_by_device_internal(
            sample_device,
            sample_notification,
        )
        assert result is True

    def test_send_notification_by_device_internal_fcm_error(
        self,
        push_service_enabled: PushService,
        mock_fcm_service_token_fail,
        sample_notification: NotificationsBase,
        sample_device: Device,
        mock_tasks_import,
    ):
        """Test internal notification method with FCM error."""
        service: PushService = push_service_enabled
        service.connector.push_service = mock_fcm_service_token_fail
        result: bool = service.sender._send_notification_by_device_internal(
            sample_device,
            sample_notification,
        )
        assert result is False


@pytest.mark.django_db
class TestPushServiceErrorHandling:
    """Test error handling scenarios."""

    def test_retry_task_scheduling_on_error(
        self,
        push_service_enabled: PushService,
        mock_fcm_service_token_fail,
        sample_notification: NotificationsBase,
        mock_tasks_import,
        sample_device: Device,
    ):
        """Test that retry tasks are scheduled on FCM errors."""
        service: PushService = push_service_enabled
        service.connector.push_service = mock_fcm_service_token_fail
        result: bool = service.sender._send_notification_by_device_internal(
            sample_device,
            sample_notification,
        )
        assert result is False


@pytest.mark.django_db
class TestPushServiceEdgeCases:
    """Test edge cases and unusual scenarios."""

    def test_send_notification_with_invalid_token(
        self,
        push_service_enabled: PushService,
        sample_notification: NotificationsBase,
        mock_tasks_import,
        sample_device: Device,
    ):
        """Test sending notification with an invalid token."""
        service: PushService = push_service_enabled
        sample_device.token = ''
        result: dict = service.sender.send_notification_by_device(
            sample_device,
            sample_notification,
        )
        assert result['success'] is False

    def test_send_notification_with_none_token(
        self,
        push_service_enabled: PushService,
        sample_notification: NotificationsBase,
        mock_tasks_import,
        sample_device: Device,
    ):
        """Test sending notification with a None token."""
        service: PushService = push_service_enabled
        sample_device.token = None

        result: dict = service.sender.send_notification_by_device(
            sample_device,
            sample_notification,
        )
        assert result['success'] is False


@pytest.mark.django_db
class TestPushServiceWithTasksIntegration:
    """Test integration with Celery tasks."""

    def test_send_notification_success(
        self,
        push_service_enabled: PushService,
        sample_notification: NotificationsBase,
        sample_device: Device,
        mock_tasks_import,
    ):
        """Test successful FCM notification does not create retry task."""
        service: PushService = push_service_enabled
        service.connector.push_service.notify.return_value = None

        result: bool = service.sender._send_notification_by_device_internal(
            sample_device, sample_notification
        )
        assert result is True
        assert not mock_tasks_import.apply_async.called

    def test_send_notification_fcm_error(
        self,
        push_service_enabled: PushService,
        sample_notification: NotificationsBase,
        sample_device: Device,
        mock_tasks_import,
    ):
        """Test FCMError triggers retry_notification_task creation."""
        service: PushService = push_service_enabled
        service.connector.push_service.notify.side_effect = FCMError(
            'FCM fail'
        )

        result: bool = service.sender._send_notification_by_device_internal(
            sample_device, sample_notification
        )
        assert result is False
        assert mock_tasks_import.apply_async.called
