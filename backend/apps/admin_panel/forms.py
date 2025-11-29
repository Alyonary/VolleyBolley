import json
import os

from django import forms
from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _


class FileUploadForm(forms.Form):
    """Simple form for uploading a single file."""

    file = forms.FileField(
        label=_('Select File'),
        help_text=_('Supported formats: JSON. Max size: 10MB'),
        widget=forms.FileInput(
            attrs={
                'class': 'form-control form-control-lg',
                'accept': '.json,',
                'id': 'id_file',
                'style': 'height: 60px; font-size: 18px;',
            }
        ),
    )

    need_update = forms.BooleanField(
        label=_('Need Update'),
        help_text=_('If checked, existing data will be updated.'),
        required=False,
        widget=forms.CheckboxInput(
            attrs={'class': 'form-check-input', 'id': 'id_clear_existing'}
        ),
    )

    def clean_file(self):
        """Validate uploaded file."""
        file = self.cleaned_data.get('file')

        if not file:
            raise ValidationError(_('File is required'))

        if file.size > 10 * 1024 * 1024:
            raise ValidationError(_('File size should not exceed 10MB'))

        file_ext = os.path.splitext(file.name)[1].lower()
        allowed_extensions = ['.json']

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

        return file
