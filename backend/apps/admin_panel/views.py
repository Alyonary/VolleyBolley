import logging

from django.contrib import messages
from django.contrib.admin.views.decorators import staff_member_required
from django.shortcuts import redirect, render
from django.utils.translation import gettext as _
from django.views.decorators.http import require_POST

from apps.admin_panel.constants import (
    MAX_FILE_SIZE,
    MONTHS_STAT_PAGINATION,
    SUPPORTED_FILE_TYPES,
)
from apps.admin_panel.forms import FileUploadForm
from apps.admin_panel.services import FileUploadService
from apps.core.models import DailyStats
from apps.core.task import collect_full_stats
from apps.notifications.push_service import PushService

logger = logging.getLogger(__name__)


@require_POST
def run_stats_task_view(request):
    """View to trigger the daily stats collection task."""
    if PushService():
        collect_full_stats.delay()
        messages.success(request, 'Daily stats task has been started!')
    else:
        messages.error(request, 'Failed to collect stats: Celery unavailable.')
    return redirect('admin_panel:admin_dashboard')


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
