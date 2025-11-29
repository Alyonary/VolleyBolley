import json
import logging
from typing import Any, Dict, List

from apps.courts.models import Court, CourtLocation
from apps.locations.models import City, Country
from apps.locations.serializers import (
    CityCreateSerializer,
    CountryCreateSerializer,
)

logger = logging.getLogger(__name__)


class FileUploadService:
    """Service for processing uploaded files."""

    def __init__(self):
        self.model_mapping = {
            'countries': {
                'model': Country,
                'serializer': CountryCreateSerializer,
                'can_update': False,
            },
            'cities': {
                'model': City,
                'serializer': CityCreateSerializer,
                'can_update': False,
            },
            'courtlocations': {
                'model': CourtLocation,
                'serializer': None,  # Assume a serializer exists
                'can_update': True,
            },
            'courts': {
                'model': Court,
                'serializer': None,  # Assume a serializer exists
                'can_update': True,
            },
        }

    def detect_file_type(self, file) -> str:
        """Automatically detect file type."""
        filename = file.name.lower()
        if filename.endswith('.json'):
            return 'json'
        return None

    def process_file(self, file, need_update: bool = False) -> Dict[str, Any]:
        """Process file based on its type."""
        file_type = self.detect_file_type(file)
        if file_type == 'json':
            return self.proccess_json_load(file, need_update)
        return {'success': False, 'error': 'Unsupported file type'}

    def proccess_json_load(
        self, file, need_update: bool = False
    ) -> Dict[str, Any]:
        """Process JSON file with model data."""
        try:
            logger.info('Processing JSON file upload')
            file.seek(0)
            content = file.read().decode('utf-8')
            data = json.loads(content)
            available_models = list(data.keys())
            if not available_models:
                logger.error('No data found in JSON file')
                return {
                    'success': False,
                    'messages': ['No data found in JSON file'],
                }
            processing_order = ('countries', 'cities', 'locations', 'courts')
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
            message = f'Error processing JSON file: {str(e)}'
            logger.error(message)
            return {
                'success': False,
                'messages': [message],
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
        can_update = model_setup.get('can_update', False)
        messages = []
        for obj_data in model_data:
            serializer = serializer_class(data=obj_data)
            logger.info(f'Validating {model_name}: {obj_data}')
            if serializer.is_valid():
                validated_data = serializer.validated_data
                try:
                    obj, created = model_class.objects.get_or_create(
                        **validated_data
                    )
                    if not created and need_update and can_update:
                        for attr, value in validated_data.items():
                            setattr(obj, attr, value)
                        obj.save()
                        status = 'Success (updated)'
                        logger.info(f'Updated {model_name}: {obj_data}')
                    else:
                        status = (
                            'Success (created)'
                            if created
                            else 'Skipped (exist)'
                        )
                    messages.append(f'{model_name}: {obj_data} — {status}')
                except Exception as e:
                    message = f'Error saving {model_name}: {str(e)}'
                    logger.error(message)
                    messages.append(message)
            else:
                error_str = '; '.join(
                    f'{field}: {", ".join(errors)}'
                    for field, errors in serializer.errors.items()
                )
                messages.append(
                    f'{model_name}: {obj_data} — Ошибка: {error_str}'
                )
        return {'messages': messages}
