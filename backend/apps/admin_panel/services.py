import json
from typing import Any, Dict, List

from apps.locations.models import City, Country
from apps.locations.serializers import (
    CitySerializer,
    CountrySerializer,
)


class FileUploadService:
    """Service for processing uploaded files."""

    def __init__(self):
        self.model_mapping = {
            'country': {
                'model': Country,
                'serializer': CountrySerializer,
            },
            'city': {
                'model': City,
                'serializer': CitySerializer,
            },
        }

    def detect_file_type(self, file) -> str:
        """Automatically detect file type."""
        filename = file.name.lower()

        if filename.endswith('.json'):
            return 'json'
        return

    def process_file(self, file, need_update: bool = False) -> Dict[str, Any]:
        """Process file based on its type."""
        file_type = self.detect_file_type(file)
        if file_type == 'json':
            return self.proccess_json_load(file, need_update)
        else:
            return {'success': False, 'error': 'Unsupported file type'}

    def proccess_json_load(
        self, file, need_update: bool = False
    ) -> Dict[str, Any]:
        """Process JSON file with model data."""
        try:
            file.seek(0)
            content = file.read().decode('utf-8')
            data = json.loads(content)

            available_models = list(data.keys())
            if not available_models:
                return {
                    'success': False,
                    'messages': ['No data found in JSON file'],
                }

            processing_order = ('country', 'city', 'location', 'court')
            messages = []

            for model_name in processing_order:
                if model_name in data and data[model_name]:
                    result = self._process_model_data(
                        model_name, data[model_name], need_update
                    )
                    messages.extend(result['messages'])

            return {
                'success': not any('Ошибка' in msg for msg in messages),
                'messages': messages,
            }
        except Exception as e:
            return {
                'success': False,
                'messages': [f'Unexpected error: {str(e)}'],
            }

    def _process_model_data(
        self,
        model_name: str,
        model_data: List[Dict],
        need_update: bool = False,
    ) -> Dict[str, Any]:
        """Process data for specific model using serializer validation."""
        if model_name not in self.model_mapping:
            return {'messages': [f'{model_name}: Unknown model']}

        model_setup = self.model_mapping[model_name]
        model_class = model_setup['model']
        serializer_class = model_setup['serializer']

        messages = []

        for obj_data in model_data:
            serializer = serializer_class(data=obj_data)
            print(f'Validating {model_name}: {obj_data}')
            if serializer.is_valid():
                validated_data = serializer.validated_data
                try:
                    print(f'Saving {model_name}: {validated_data}')
                    obj, created = model_class.objects.get_or_create(
                        **validated_data
                    )
                    status = (
                        'Success (created)' if created else 'Skipped (exist)'
                    )
                    messages.append(f'{model_name}: {obj_data} — {status}')
                except Exception as e:
                    print(f'Error saving {model_name}: {e}')
                    messages.append(
                        f'{model_name}: {obj_data} — Ошибка: {str(e)}'
                    )
            else:
                error_str = '; '.join(
                    f'{field}: {", ".join(errors)}'
                    for field, errors in serializer.errors.items()
                )
                messages.append(
                    f'{model_name}: {obj_data} — Ошибка: {error_str}'
                )
        return {'messages': messages}
