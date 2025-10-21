from threading import Thread

import pytest
from pyfcm.errors import FCMError

from apps.notifications.constants import NotificationTypes
from apps.notifications.models import Notifications
from apps.notifications.push_service import PushService


class TestPushServiceSingleton:
    """Test PushService singleton behavior."""

    def test_singleton_creates_only_one_instance(self):
        """Test that PushService creates only one instance."""
        service1 = PushService()
        service2 = PushService()
        assert service1 is service2

    def test_singleton_thread_safety(self, reset_push_service):
        """Test singleton is thread-safe."""
        instances = []

        def create_instance():
            instances.append(PushService())

        threads = [Thread(target=create_instance) for _ in range(10)]
        for thread in threads:
            thread.start()
        for thread in threads:
            thread.join()
        first_instance = instances[0]
        for instance in instances[1:]:
            assert instance is first_instance


class TestPushServiceInitialization:
    """Test PushService initialization scenarios."""

    def test_successful_initialization_both_services_available(
        self, push_service_enabled
    ):
        """Test success initialization when FCM and Celery are available."""
        service = push_service_enabled

        assert service.enable is True
        assert service.celery_available is True
        assert service._initialized is True
        assert hasattr(service, 'push_service')

    def test_initialization_no_services_available(self, push_service_disabled):
        """Test initialization when no services are available."""
        service = push_service_disabled

        assert service.enable is False
        assert service.celery_available is False
        assert service._initialized is True

    def test_initialization_fcm_only_available(self, push_service_fcm_only):
        """Test initialization when FCM is available but Celery is not."""
        service = push_service_fcm_only

        assert service.enable is False
        assert service.celery_available is False
        assert service._initialized is True

    def test_initialization_with_fcm_error(
        self, reset_push_service, monkeypatch
    ):
        """Test initialization when FCM throws an error."""

        def mock_initialize_firebase(self):
            return False

        def mock_check_celery_availability(self):
            return True

        monkeypatch.setattr(
            PushService,
            '_initialize_firebase',
            mock_initialize_firebase
        )
        monkeypatch.setattr(
            PushService,
            '_check_celery_availability',
            mock_check_celery_availability,
        )

        service = PushService()
        assert service.celery_available is True
        assert service.enable is False
        assert service._initialized is True


class TestPushServiceStatusMethods:
    """Test PushService status and checking methods."""

    def test_bool_method_all_services_available(self, push_service_enabled):
        """Test __bool__ method when all services are available."""
        service = push_service_enabled
        assert service.enable is True
        assert service.celery_available is True
        assert service._initialized is True
        assert bool(service) is True

    def test_bool_method_services_unavailable(self, push_service_disabled):
        """Test __bool__ method when services are unavailable."""
        service = push_service_disabled
        assert service.enable is False
        assert service.celery_available is False
        assert service._initialized is True
        assert bool(service) is False

    def test_get_status_returns_correct_dict(self, push_service_enabled):
        """Test get_status returns correct status dictionary."""
        service = push_service_enabled
        status = service.get_status()

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

    def test_get_status_disabled_service(self, push_service_disabled):
        """Test get_status for disabled service."""
        service = push_service_disabled
        status = service.get_status()

        assert status['notifications_enabled'] is False
        assert status['fcm_available'] is False
        assert status['celery_available'] is False
        assert status['initialized'] is True


@pytest.mark.django_db
class TestPushServiceNotificationMethods:
    """Test notification sending methods."""

    def test_send_notification_by_device_success(
        self, push_service_enabled, sample_notification, sample_device
    ):
        """Test successful single device notification."""
        service: PushService = push_service_enabled
        result = service.send_notification_by_device(
            sample_device,
            sample_notification,
        )

        assert result is True

    def test_send_notification_by_device_with_game_id(
        self,
        push_service_enabled,
        in_game_notification_type,
        sample_device,
        game_for_notification

    ):
        """Test single device notification with game_id."""

        service = push_service_enabled
        assert game_for_notification is not None
        notif_in_db = Notifications.objects.filter(
            player=sample_device.player,
            game=game_for_notification,
        ).first()
        assert notif_in_db is None

        result = service.send_notification_by_device(
            sample_device,
            in_game_notification_type,
            event_id=game_for_notification.id,
        )
        assert result is True
        #check that notification was created in DB
        notif_in_db = Notifications.objects.filter(
            player=sample_device.player,
            game=game_for_notification,
        ).first()
        assert notif_in_db is not None

    def test_send_notification_by_device_service_disabled(
        self, push_service_disabled, sample_notification, sample_device
    ):
        """Test notification when service is disabled."""
        service = push_service_disabled
        result = service.send_notification_by_device(
            sample_device,
            sample_notification,
        )
        assert result is None

    def test_send_notification_by_device_fcm_error(
        self,
        push_service_enabled,
        mock_fcm_service_fail,
        sample_notification,
        mock_tasks_import,
        sample_device,
    ):
        """Test notification with FCM error."""
        service = push_service_enabled
        service.push_service = mock_fcm_service_fail

        result = service.send_notification_by_device(
            sample_device,
            sample_notification,
        )
        assert result is False

    def test_send_push_notifications_multiple_devices(
        self,
        push_service_enabled,
        sample_notification,
        mock_fcm_service_fail,
        mock_tasks_import,
        devices,
    ):
        """Test sending to multiple devices."""
        service = push_service_enabled
        devices = devices['active_devices']
        result = service.send_push_notifications(devices, sample_notification)

        assert isinstance(result, dict)
        assert result['total_devices'] == 3
        assert result['successful'] == 3
        assert result['failed'] == 0

        service.push_service = mock_fcm_service_fail
        result_with_errors = service.send_push_notifications(
            devices, sample_notification
        )
        assert isinstance(result_with_errors, dict)
        assert result_with_errors['total_devices'] == 3
        assert result_with_errors['successful'] == 0
        assert result_with_errors['failed'] == 3

    def test_send_push_notifications_empty_tokens_list(
        self,
        push_service_enabled,
        sample_notification,
    ):
        """Test sending to empty devices list."""
        service = push_service_enabled
        devices = []

        result = service.send_push_notifications(devices, sample_notification)

        assert isinstance(result, dict)
        assert result['total_devices'] == 0
        assert result['successful'] == 0
        assert result['failed'] == 0


@pytest.mark.django_db
class TestPushServiceInternalMethods:
    """Test internal helper methods."""

    def test_send_notification_by_device_internal_success(
        self, push_service_enabled, sample_notification, sample_device
    ):
        """Test internal notification method success."""
        service = push_service_enabled
        result = service._send_notification_by_device_internal(
            sample_device,
            sample_notification,
        )
        assert result is True

    def test_send_notification_by_device_internal_fcm_error(
        self,
        push_service_enabled,
        mock_fcm_service_token_fail,
        sample_notification,
        sample_device,
        mock_tasks_import,
    ):
        """Test internal notification method with FCM error."""
        service = push_service_enabled
        service.push_service = mock_fcm_service_token_fail
        result = service._send_notification_by_device_internal(
            sample_device,
            sample_notification,
        )
        assert result is False


@pytest.mark.django_db
class TestPushServiceErrorHandling:
    """Test error handling scenarios."""

    def test_retry_task_scheduling_on_error(
        self,
        push_service_enabled,
        mock_fcm_service_token_fail,
        sample_notification,
        mock_tasks_import,
        sample_device,
    ):
        """Test that retry tasks are scheduled on FCM errors."""
        service = push_service_enabled
        service.push_service = mock_fcm_service_token_fail
        result = service._send_notification_by_device_internal(
            sample_device,
            sample_notification,
        )
        assert result is False

    def test_exception_handling_in_process_notifications(
        self, push_service_enabled, monkeypatch
    ):
        """Test exception handling in process_notifications_by_type."""
        service = push_service_enabled

        def mock_send_push_notifications(*args, **kwargs):
            raise Exception('Notification creation failed')

        monkeypatch.setattr(
            service,
            'send_push_notifications',
            mock_send_push_notifications
        )

        result = service.process_notifications_by_type(
            NotificationTypes.GAME_REMINDER, event_id=1
        )

        assert result['status'] is False
        assert 'Notification creation failed' in result['message']


@pytest.mark.django_db
class TestPushServiceEdgeCases:
    """Test edge cases and unusual scenarios."""

    def test_send_notification_with_invalid_token(
        self,
        push_service_enabled,
        sample_notification,
        mock_tasks_import,
        sample_device,
    ):
        """Test sending notification with an invalid token."""
        service = push_service_enabled
        sample_device.token = ''
        result = service.send_notification_by_device(
            sample_device,
            sample_notification,
        )
        assert result is False

    def test_send_notification_with_none_token(
        self,
        push_service_enabled,
        sample_notification,
        mock_tasks_import,
        sample_device,
    ):
        """Test sending notification with a None token."""
        service = push_service_enabled
        sample_device.token = None

        result = service.send_notification_by_device(
            sample_device,
            sample_notification,
        )
        assert result is False


@pytest.mark.django_db
class TestPushServiceWithTasksIntegration:
    """Test integration with Celery tasks."""

    def test_send_notification_success(
        self,
        push_service_enabled,
        sample_notification,
        sample_device,
        mock_tasks_import,
    ):
        """Test successful FCM notification does not create retry task."""
        service = push_service_enabled
        service.push_service.notify.return_value = None

        result = service._send_notification_by_device_internal(
            sample_device, sample_notification
        )
        assert result is True
        assert not mock_tasks_import.apply_async.called

    def test_send_notification_fcm_error(
        self,
        push_service_enabled,
        sample_notification,
        sample_device,
        mock_tasks_import,
    ):
        """Test FCMError triggers retry_notification_task creation."""
        service = push_service_enabled
        service.push_service.notify.side_effect = FCMError('FCM fail')

        result = service._send_notification_by_device_internal(
            sample_device, sample_notification
        )
        assert result is False
        assert mock_tasks_import.apply_async.called
