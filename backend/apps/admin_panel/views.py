import logging

from volleybolley.celery import CeleryInspector
from celery.exceptions import CeleryError
from django.contrib import messages
from django.contrib.admin.views.decorators import staff_member_required
from django.shortcuts import redirect, render
from django.utils.translation import gettext as _
from django.views.decorators.http import require_POST

from apps.admin_panel.constants import (
    MAX_FILE_SIZE,
    MONTHS_STAT_PAGINATION,
    SUPPORTED_FILE_TYPES,
    SendType,
    UploadServiceMessages,
)
from apps.admin_panel.forms import FileUploadForm, NotificationSendForm
from apps.admin_panel.services import FileUploadService
from apps.core.models import DailyStats
from apps.core.task import collect_full_project_stats
from apps.event.models import Game, Tourney
from apps.notifications.constants import (
    NotificationTypes,
    PushServiceMessages,
)
from apps.notifications.push_service import PushService
from apps.notifications.tasks import (
    send_event_notification_task,
    send_notification_to_player_task,
)
from apps.players.models import Player

logger = logging.getLogger(__name__)


@require_POST
def run_stats_task_view(request):
    """View to trigger the daily stats collection task."""
    if PushService():
        collect_full_project_stats.delay()
        messages.success(request, 'Daily stats task has been started!')
    else:
        messages.error(request, 'Failed to collect stats: Celery unavailable.')
    return redirect('admin_panel:admin_dashboard')


@staff_member_required
def notifications_view(request):
    """Admin view for managing notifications."""
    inspector = CeleryInspector()
    if request.method == 'POST':
        error_occured = False
        form = NotificationSendForm(request.POST)
        if not form.is_valid():
            messages.warning(request, form.errors)
        else:
            player_id = form.cleaned_data.get('player_id', None)
            event_id = form.cleaned_data.get('event_id', None)
            send_type = form.cleaned_data['send_type']
            notification_type = form.cleaned_data['notification_type']
            if send_type == SendType.SEND_TO_PLAYER:
                player = Player.objects.filter(id=player_id).first()
                if not player:
                    error_occured = True
                    messages.error(
                        request, _(PushServiceMessages.PLAYER_NOT_FOUND)
                    )
            elif send_type == SendType.SEND_TO_EVENT:
                if notification_type in NotificationTypes.FOR_GAMES:
                    event_model = Game
                elif notification_type in NotificationTypes.FOR_TOURNEYS:
                    event_model = Tourney
                event = event_model.objects.filter(id=event_id).first()
                if not event:
                    error_occured = True
                    messages.error(
                        request, PushServiceMessages.EVENT_NOT_FOUND
                    )
            if not error_occured:
                task_status = create_notification_task(
                    event_id, player_id, send_type, notification_type
                )
                if not task_status['success']:
                    messages.error(request, _(task_status['message']))
                else:
                    messages.success(request, _(task_status['message']))
    else:
        form = NotificationSendForm()
    context = {
        'title': _('Notifications Management'),
        'page_header': _('Manage Notifications'),
        'page_description': _(
            'View and manage push notifications sent to users.'
        ),
        'push_service_enabled': True,
        'form': form,
    }
    return render(request, 'admin_panel/notifications.html', context)


@staff_member_required
def upload_file(request):
    """File upload page in admin."""

    if request.method == 'POST':
        form = FileUploadForm(request.POST, request.FILES)
        if form.is_valid():
            show_only_failure = form.cleaned_data.get(
                'show_only_failure', False
            )
            return process_file_upload(request, form, show_only_failure)
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


def process_file_upload(
    request, form: FileUploadForm, show_only_failure: bool
):
    """Process uploaded file."""

    file = form.cleaned_data['file']
    try:
        upload_service = FileUploadService()
        result = upload_service.process_file(file=file)
        summarize_results = upload_service.summarize_results(result)
        summary_message = summarize_results.get('message', '')
        if not summarize_results.get('success', False):
            messages.error(
                request,
                _(UploadServiceMessages.ERROR_DOWNLOAD + ' %(error)s')
                % {'error': result.get('error', 'Unknown error')}
                + f' {summary_message}',
            )
        else:
            messages.success(
                request,
                _(UploadServiceMessages.SUCCESS_DOWNLOAD) + summary_message,
            )
        if 'messages' in result:
            request.session['upload_messages'] = result['messages']
        for msg in result.get('messages', []):
            msg_lower = msg.lower()
            if 'error' in msg_lower:
                messages.error(request, msg)
                continue
            if 'created' in msg_lower:
                if show_only_failure:
                    messages.success(request, msg)
                continue
            messages.info(request, msg)
    except Exception as e:
        messages.error(
            request,
            _(UploadServiceMessages.UNEXPECTED_ERROR + '  %(error)s')
            % {'error': str(e)},
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


@staff_member_required
def dashboard_view(request):
    """Admin dashboard view showing key metrics."""

    stats = DailyStats.objects.get_stats_by_month(MONTHS_STAT_PAGINATION)
    players_chart_labels = []
    players_chart_data = []
    games_chart_labels = []
    games_chart_data = []
    total_players = 0
    total_games = 0
    total_tourneys = 0
    active_games = 0
    active_tourneys = 0

    for stat in stats:
        label = stat['month'].strftime('%Y-%m')
        players_chart_labels.append(label)
        players_chart_data.append(stat.get('players_registered', 0))
        games_chart_labels.append(label)
        games_chart_data.append(stat.get('games_created', 0))
        total_players += stat.get('players_registered', 0)
        total_games += stat.get('games_created', 0)
        total_tourneys += stat.get('tourneys_created', 0)

    context = {
        'total_players': total_players,
        'total_games': total_games,
        'total_tourneys': total_tourneys,
        'active_games': active_games,
        'active_tourneys': active_tourneys,
        'players_chart_labels': players_chart_labels,
        'players_chart_data': players_chart_data,
        'games_chart_labels': games_chart_labels,
        'games_chart_data': games_chart_data,
    }
    return render(request, 'admin_panel/admin_dashboard.html', context)


def create_notification_task(
    event_id: int | None,
    player_id: int | None,
    send_type: str,
    notification_type: str,
    inspector: CeleryInspector
) -> dict[str, bool]:
    """
    Create notification task.
    Attempting to create notification by celery task.
    Return dict with status and message about error(if thats occured).
    """
    if send_type == SendType.SEND_TO_EVENT:
        return inspector.delay_task(
            task=send_event_notification_task,
            task_args={
                'event_id':event_id, 'notification_type': notification_type
            }
        )
    elif send_type == SendType.SEND_TO_PLAYER:
        return inspector.delay_task(
            task=send_notification_to_player_task,
            task_args={
                'player_id': player_id,
                'event_id': event_id,
                'notification_type':notification_type
            }
        )
    else:
        m = f'Uknown type {notification_type} for {send_type}notification'
        logger.error(m)
        return {'success': False, 'message': m}
