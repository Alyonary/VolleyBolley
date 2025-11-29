from datetime import datetime

from django.contrib import messages
from django.contrib.admin.views.decorators import staff_member_required
from django.db.models import Count
from django.db.models.functions import TruncMonth
from django.shortcuts import redirect, render
from django.utils.translation import gettext as _

from apps.admin_panel.forms import FileUploadForm
from apps.admin_panel.services import FileUploadService
from apps.event.models import Game, Tourney
from apps.players.models import Player


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

    total_players = Player.objects.count()
    total_games = Game.objects.count()
    total_tourneys = Tourney.objects.count()
    active_games = Game.objects.filter(is_active=True).count()
    active_tourneys = Tourney.objects.filter(is_active=True).count()

    games_by_month = (
        Game.objects.annotate(month=TruncMonth('created_at'))
        .values('month')
        .annotate(count=Count('id'))
        .order_by('month')
    )
    games_chart_labels = [g['month'].strftime('%b %Y') for g in games_by_month]
    games_chart_data = [g['count'] for g in games_by_month]

    players_by_month = Player.objects.registrations_by_month()
    players_by_month_dict = {
        p['month']: p['count'] for p in players_by_month if p['month']
    }

    if players_by_month_dict:
        first_month = min(players_by_month_dict)
        last_month = max(players_by_month_dict)
    else:
        first_month = last_month = datetime.today().replace(day=1)

    months = []
    current = first_month
    while current <= last_month:
        months.append(current)
        year = current.year + (current.month // 12)
        month = (current.month % 12) + 1
        current = current.replace(year=year, month=month)

    players_chart_labels = [m.strftime('%b %Y') for m in months]
    players_chart_data = [players_by_month_dict.get(m, 0) for m in months]

    context = {
        'total_players': total_players,
        'total_games': total_games,
        'total_tourneys': total_tourneys,
        'active_games': active_games,
        'active_tourneys': active_tourneys,
        'games_chart_labels': games_chart_labels,
        'games_chart_data': games_chart_data,
        'players_chart_labels': players_chart_labels,
        'players_chart_data': players_chart_data,
    }
    return render(request, 'admin_panel/admin_dashboard.html', context)
