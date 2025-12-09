import logging
from datetime import datetime

from django.conf import settings
from django.contrib import messages
from django.contrib.admin.views.decorators import staff_member_required
from django.db.models import Sum
from django.shortcuts import redirect, render
from django.utils.translation import gettext as _
from django.views.decorators.http import require_POST

from apps.admin_panel.constants import MAX_FILE_SIZE, SUPPORTED_FILE_TYPES
from apps.admin_panel.forms import FileUploadForm
from apps.admin_panel.services import FileUploadService
from apps.core.models import DailyStats
from apps.core.task import collect_daily_stats, collect_full_stats
from apps.event.models import Game, Tourney
from apps.notifications.push_service import PushService
from apps.players.models import Player

logger = logging.getLogger(__name__)


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
def upload_file(request):
    """File upload page in admin."""

    if request.method == 'POST':
        form = FileUploadForm(request.POST, request.FILES)
        if form.is_valid():
            return process_file_upload(request, form)
    else:
        form = FileUploadForm()

    supported_models = [
        'countries',
        'cities',
        'courts',
    ]
    if settings.DEBUG:
        supported_models.extend(['players', 'games', 'tourneys'])
    form_description = (
        ', '.join([ft.upper() for ft in SUPPORTED_FILE_TYPES])
        + f' (max {MAX_FILE_SIZE // (1024 * 1024)}MB)'
    )
    context = {
        'title': _('Data File Upload'),
        'form': form,
        'supported_models': supported_models,
        'form_description': form_description,
        'page_header': _('Upload Data Files'),
        'page_description': _('Import models data from JSON or Excel files.'),
        'model_fields_info': get_model_expected_fields(),
    }

    return render(request, 'admin_panel/upload.html', context)


@staff_member_required
def dashboard_view(request):
    """Admin dashboard view showing key metrics."""

    active_games = Game.objects.filter(is_active=True).count()
    active_tourneys = Tourney.objects.filter(is_active=True).count()

    collect_full_stats()
    stats = DailyStats.objects.all().order_by('-date')[:1]
    total_players = total_games = total_tourneys = 0
    if stats:
        total_players = (
            DailyStats.objects.aggregate(total=Sum('players_registered'))[
                'total'
            ]
            or 0
        )
        total_games = (
            DailyStats.objects.aggregate(total=Sum('games_created'))['total']
            or 0
        )
        total_tourneys = (
            DailyStats.objects.aggregate(total=Sum('tourneys_created'))[
                'total'
            ]
            or 0
        )

    players_chart_labels, players_chart_data = get_stats_by_month(
        'players_registered'
    )
    games_chart_labels, games_chart_data = get_stats_by_month('games_created')

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


def get_qs_by_month(model: Game | Player) -> tuple[list[str], list[int]]:
    """Returns the number of objects grouped by month.
    Args:
        model (Game | Player): The model to query.
    Returns:
        list[Game | Player]: List of objects grouped by month.
    """
    objs_by_month = model.objects.get_objs_by_month()
    objs_by_month_dict = {
        obj['month']: obj['count'] for obj in objs_by_month if obj['month']
    }
    if objs_by_month_dict:
        first_month = min(objs_by_month_dict)
        last_month = max(objs_by_month_dict)
    else:
        first_month = last_month = datetime.today().replace(day=1)
    months = []
    current = first_month
    while current <= last_month:
        months.append(current)
        year = current.year + (current.month // 12)
        month = (current.month % 12) + 1
        current = current.replace(year=year, month=month)
    objs_chart_labels = [m.strftime('%b %Y') for m in months]
    objs_chart_data = [objs_by_month_dict.get(m, 0) for m in months]
    return objs_chart_labels, objs_chart_data


def get_stats_by_month(stat_type: str) -> tuple[list[str], list[int]]:
    """Returns the statistics data grouped by month.
    Args:
        stat_type (str): The type of statistic to query
            (e.g., 'players_registered').
    Returns:
        tuple: A tuple containing two lists - labels and data.
    """
    stats_by_month = DailyStats.objects.get_stats_by_month(stat_type)
    stats_by_month_dict = {
        stat['month']: stat['total']
        for stat in stats_by_month
        if stat['month']
    }
    if stats_by_month_dict:
        first_month = min(stats_by_month_dict)
        last_month = max(stats_by_month_dict)
    else:
        first_month = last_month = datetime.today().replace(day=1)
    months = []
    current = first_month
    while current <= last_month:
        months.append(current)
        year = current.year + (current.month // 12)
        month = (current.month % 12) + 1
        current = current.replace(year=year, month=month)
    stats_chart_labels = [m.strftime('%b %Y') for m in months]
    stats_chart_data = [stats_by_month_dict.get(m, 0) for m in months]
    return stats_chart_labels, stats_chart_data


def process_file_upload(request, form):
    """Process uploaded file."""

    file = form.cleaned_data['file']

    try:
        upload_service = FileUploadService()
        result = upload_service.process_file(
            file=file,
        )
        if not result.get('success', False):
            messages.error(
                request,
                _('❌ File processing failed: %(error)s')
                % {'error': result.get('error', 'Unknown error')}
            )
            if result.get('messages'):
                messages.info(
                    request,
                    _('Details: %(details)s')
                    % {'details': '; '.join(result['messages'])}
                )
            return redirect('admin_panel:upload_file')
        if 'messages' in result:
            request.session['upload_messages'] = result['messages']
        for msg in result.get('messages', []):
            msg_lower = msg.lower()
            if 'updated' in msg_lower:
                messages.warning(request, msg)
            elif 'error' in msg_lower:
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


def get_model_expected_fields():
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
