import logging

from django.contrib import messages
from django.contrib.admin.views.decorators import staff_member_required
from django.shortcuts import redirect, render
from django.utils.translation import gettext as _
from django.views.decorators.http import require_POST

from apps.admin_panel.constants import (
    MAX_FILE_SIZE,
    SUPPORTED_FILE_TYPES,
    SendType,
)
from apps.admin_panel.forms import FileUploadForm, NotificationSendForm
from apps.admin_panel.services import FileUploadService
from apps.core.task import collect_daily_stats
from apps.notifications.push_service import PushService

logger = logging.getLogger(__name__)


@staff_member_required
def notifications_view(request):
    """Admin view for managing notifications."""
    push_service = PushService()
    if request.method == 'POST':
        form = NotificationSendForm(request.POST)
        if form.is_valid():
            send_type = form.cleaned_data['send_type']
            if send_type == SendType.SEND_TO_PLAYER.value:
                player_id = form.cleaned_data['player_id']
                result = push_service.send_to_player(
                    player_id=player_id,
                    notification_type=form.cleaned_data['notification_type'],
                )
            elif send_type == SendType.SEND_TO_EVENT.value:
                event_id = form.cleaned_data['event_id']
                result = push_service.send_push_for_event(
                    event_id=event_id,
                    notification_type=form.cleaned_data['notification_type'],
                )
            if result.get('success'):
                messages.success(
                    request, _('✅ Notification sent successfully.')
                )
            else:
                messages.error(
                    request,
                    _('❌ Failed to send notification: %(error)s')
                    % {'error': result.get('error', 'Unknown error')},
                )

    else:
        form = NotificationSendForm()
    context = {
        'title': _('Notifications Management'),
        'page_header': _('Manage Notifications'),
        'page_description': _(
            'View and manage push notifications sent to users.'
        ),
        'push_service_enabled': push_service.enable,
        'form': form,
    }
    return render(request, 'admin_panel/notifications.html', context)


@staff_member_required
def upload_file(request):
    """File upload page in admin."""

    if request.method == 'POST':
        form = FileUploadForm(request.POST, request.FILES)
        if form.is_valid():
            stats_detail = form.cleaned_data.get('stats_detail', False)
            return process_file_upload(request, form, stats_detail)
    else:
        form = FileUploadForm()

    model_fields_info = get_model_expected_fields()
    form_description = (
        ', '.join([ft.upper() for ft in SUPPORTED_FILE_TYPES])
        + f' (max {MAX_FILE_SIZE // (1024 * 1024)}MB)'
    )
    context = {
        'title': _('Data File Upload'),
        'form': form,
        'supported_models': [
            name['model']
            for name in model_fields_info
            if (
                name.get('excel_fields', False)
                and name.get('json_fields', False)
            )
        ],
        'form_description': form_description,
        'page_header': _('Upload Data Files'),
        'page_description': _('Import models data from JSON or Excel files.'),
        'model_fields_info': model_fields_info,
    }

    return render(request, 'admin_panel/upload.html', context)


def process_file_upload(request, form: FileUploadForm, stats_detail: bool):
    """Process uploaded file."""

    file = form.cleaned_data['file']
    try:
        upload_service = FileUploadService()
        result = upload_service.process_file(file=file)
        if not stats_detail:
            result = upload_service.summarize_results(result)
        if not result.get('success', False):
            messages.error(
                request,
                _('❌ File processing failed: %(error)s')
                % {'error': result.get('error', 'Unknown error')},
            )
            if result.get('messages'):
                messages.info(
                    request,
                    _('Details: %(details)s')
                    % {'details': '; '.join(result['messages'])},
                )
            return redirect('admin_panel:upload_file')
        if 'messages' in result:
            request.session['upload_messages'] = result['messages']
        for msg in result.get('messages', []):
            msg_lower = msg.lower()
            if 'error' in msg_lower:
                messages.error(request, msg)
            elif 'created' in msg_lower:
                messages.success(request, msg)
            else:
                messages.info(request, msg)

    except Exception as e:
        messages.error(
            request, _('❌ Unexpected error: %(error)s') % {'error': str(e)}
        )

    return redirect('admin_panel:upload_file')


def get_model_expected_fields() -> list[dict[str, list[str] | str]]:
    """Get expected fields for each model in upload service."""

    upload_service = FileUploadService()
    result = []
    for name, mapping in upload_service.model_mapping_class.items():
        entry = {'model': name}
        if getattr(mapping, 'serializer', None):
            entry['excel_fields'] = list(
                getattr(mapping, 'expected_fields', [])
            )
            serializer_class = mapping.serializer
            if serializer_class:
                serializer = serializer_class()
                json_fields = []
                for field_name, field in serializer.fields.items():
                    if hasattr(field, 'fields'):
                        nested = list(field.fields.keys())
                        json_fields.append({field_name: nested})
                    else:
                        json_fields.append(field_name)
                entry['json_fields'] = json_fields
        result.append(entry)
    return result


@require_POST
def run_stats_task_view(request):
    """View to trigger the daily stats collection task."""
    if PushService():
        collect_daily_stats.delay()
        messages.success(request, 'Daily stats task has been started!')
    else:
        messages.error(request, 'Failed to collect stats: Celery unavailable.')
    return redirect('admin_panel:admin_dashboard')


@staff_member_required
def dashboard_view(request):
    """Admin dashboard view showing key metrics."""

    # временно
    # Тестовые данные для демонстрации дашборда
    dashboard_test_data = {
        'players_chart_labels': [
            '2025-07',
            '2025-08',
            '2025-09',
            '2025-10',
            '2025-11',
            '2025-12',
        ],
        'players_chart_data': [120, 150, 180, 210, 250, 300],
        'games_chart_labels': [
            '2025-07',
            '2025-08',
            '2025-09',
            '2025-10',
            '2025-11',
            '2025-12',
        ],
        'games_chart_data': [45, 60, 80, 100, 130, 170],
        'total_players': 300,
        'total_games': 170,
        'total_tourneys': 25,
        'active_games': 7,
        'active_tourneys': 2,
    }

    context = {
        'total_players': dashboard_test_data['total_players'],
        'total_games': dashboard_test_data['total_games'],
        'total_tourneys': dashboard_test_data['total_tourneys'],
        'active_games': dashboard_test_data['active_games'],
        'active_tourneys': dashboard_test_data['active_tourneys'],
        'players_chart_labels': dashboard_test_data['players_chart_labels'],
        'players_chart_data': dashboard_test_data['players_chart_data'],
        'games_chart_labels': dashboard_test_data['games_chart_labels'],
        'games_chart_data': dashboard_test_data['games_chart_data'],
    }
    return render(request, 'admin_panel/admin_dashboard.html', context)
