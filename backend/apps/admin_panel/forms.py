import json
import os

from backend.apps.notifications.constants import NotificationTypes
from django import forms
from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _

from apps.admin_panel.constants import MAX_FILE_SIZE, SEND_TYPE_CHOICES


class FileUploadForm(forms.Form):
    """Simple form for uploading a single file."""

    file = forms.FileField(
        label=_('Select File'),
        help_text=_('Supported formats: JSON. Max size: 10MB'),
        widget=forms.FileInput(
            attrs={
                'class': 'form-control form-control-lg',
                'accept': '.json, .xlsx, .xls',
                'id': 'id_file',
                'style': 'height: 60px; font-size: 18px;',
            }
        ),
    )
    stats_detail = forms.BooleanField(
        label=_('Detailed statistics'),
        required=False,
        help_text=_('Enable detailed statistics for the uploaded data.'),
        widget=forms.CheckboxInput(attrs={'class': 'checkbox-input'}),
    )

    def clean_file(self):
        """Validate uploaded file."""
        file = self.cleaned_data.get('file')
        if not file:
            raise ValidationError(_('File is required'))
        if file.size > MAX_FILE_SIZE:
            raise ValidationError(_('File size should not exceed 10MB'))
        file_ext = os.path.splitext(file.name)[1].lower()
        allowed_extensions = ['.json', '.xlsx', '.xls']
        if file_ext not in allowed_extensions:
            raise ValidationError(
                _('Unsupported file format. Allowed: %(formats)s')
                % {'formats': ', '.join(allowed_extensions)}
            )
        if file_ext == '.json':
            try:
                file.seek(0)
                content = file.read().decode('utf-8')
                json.loads(content)
                file.seek(0)
            except (UnicodeDecodeError, json.JSONDecodeError) as e:
                raise ValidationError(
                    _('Invalid JSON file: %(error)s') % {'error': str(e)}
                ) from e
        elif file_ext in ['.xlsx', '.xls']:
            try:
                import openpyxl

                file.seek(0)
                wb = openpyxl.load_workbook(file)
                ws = wb.active
                headers = [
                    cell.value
                    for cell in next(ws.iter_rows(min_row=1, max_row=1))
                ]
                if not headers or any(
                    h is None or str(h).strip() == '' for h in headers
                ):
                    raise ValidationError(
                        _('Excel file must have non-empty header row')
                    )
                file.seek(0)
            except Exception as e:
                raise ValidationError(
                    _('Invalid Excel file: %(error)s') % {'error': str(e)}
                ) from e
        return file


class NotificationSendForm(forms.Form):
    send_type = forms.ChoiceField(
        choices=SEND_TYPE_CHOICES,
        label=_('Send Type'),
        widget=forms.Select(
            attrs={'class': 'form-select', 'id': 'id_send_type'}
        ),
    )
    player_id = forms.IntegerField(
        label=_('Player ID'),
        required=False,
        widget=forms.NumberInput(
            attrs={'class': 'form-control', 'id': 'id_player_id'}
        ),
    )
    event_id = forms.IntegerField(
        label=_('Event ID'),
        required=False,
        widget=forms.NumberInput(
            attrs={'class': 'form-control', 'id': 'id_event_id'}
        ),
    )
    notification_type = forms.ChoiceField(
        choices=NotificationTypes.CHOICES,
        label=_('Notification Type'),
        widget=forms.Select(
            attrs={'class': 'form-select', 'id': 'id_notification_type'}
        ),
    )

    def clean(self):
        cleaned_data = super().clean()
        send_type = cleaned_data.get('send_type')
        player_id = cleaned_data.get('player_id')
        event_id = cleaned_data.get('event_id')

        if send_type == 'send_to_device' and not player_id:
            self.add_error(
                'player_id', _('Player ID is required for device notification')
            )
        if send_type == 'send_to_event' and not event_id:
            self.add_error(
                'event_id', _('Event ID is required for event notification')
            )
        return cleaned_data
