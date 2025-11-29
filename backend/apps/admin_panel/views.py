from django.contrib import messages
from django.contrib.admin.views.decorators import staff_member_required
from django.shortcuts import redirect, render
from django.utils.translation import gettext as _

from apps.admin_panel.forms import FileUploadForm
from apps.admin_panel.services import FileUploadService


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
