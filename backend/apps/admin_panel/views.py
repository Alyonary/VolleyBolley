import logging
from datetime import datetime

from django.contrib import messages
from django.contrib.admin.views.decorators import staff_member_required
from django.db.models import Sum
from django.shortcuts import redirect, render
from django.utils.translation import gettext as _

from apps.admin_panel.forms import FileUploadForm
from apps.admin_panel.services import FileUploadService
from apps.core.models import DailyStats
from apps.event.models import Game, Tourney
from apps.players.models import Player

logger = logging.getLogger(__name__)


@staff_member_required
def upload_file(request):
    """File upload page in admin."""

    if request.method == 'POST':
        form = FileUploadForm(request.POST, request.FILES)
        if form.is_valid():
            return process_file_upload(request, form)
    else:
        form = FileUploadForm()

    upload_stats = {
        'total_uploads': 0,
        'successful_uploads': 0,
        'failed_uploads': 0,
    }

    context = {
        'title': _('Data File Upload'),
        'form': form,
        'page_header': _('Upload Data Files'),
        'page_description': _(
            'Import countries, cities, locations, courts from JSON files'
        ),
        'upload_stats': upload_stats,
    }

    return render(request, 'admin_panel/upload.html', context)


def process_file_upload(request, form):
    """Process uploaded file."""

    file = form.cleaned_data['file']
    need_update = form.cleaned_data.get('need_update', False)

    try:
        upload_service = FileUploadService()
        result = upload_service.process_file(
            file=file, need_update=need_update
        )

        if 'messages' in result:
            request.session['upload_messages'] = result['messages']

        if result['success']:
            messages.success(
                request,
                _(
                    '✅ File "%(filename)s" processed successfully! '
                    'Total: %(count)d records.'
                )
                % {
                    'filename': file.name,
                    'count': len(result.get('messages', [])),
                },
            )
        else:
            for msg in result.get('messages', []):
                if 'Success' in msg:
                    messages.success(request, msg)
                elif 'Skipped' in msg:
                    messages.warning(request, msg)
                else:
                    messages.error(request, msg)
            if 'error' in result:
                messages.error(
                    request,
                    _('❌ Error processing file: %(error)s')
                    % {'error': result['error']},
                )

    except Exception as e:
        messages.error(
            request, _('❌ Unexpected error: %(error)s') % {'error': str(e)}
        )

    return redirect('admin_panel:upload_file')


@staff_member_required
def dashboard_view(request):
    """Admin dashboard view showing key metrics."""
    from apps.event.models import Game

    # Актуальные значения на момент запроса
    active_games = Game.objects.filter(is_active=True).count()
    active_tourneys = Tourney.objects.filter(is_active=True).count()

    # Последняя доступная статистика (например, за вчера)
    stats = DailyStats.objects.order_by('-date').first()
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
