import json
import logging
import os
from typing import Any, Dict, List

import openpyxl
from django.conf import settings

from apps.admin_panel.constants import MAX_FILE_SIZE, SUPPORTED_FILE_TYPES
from apps.core.models import CurrencyType, GameLevel
from apps.core.serializers import (
    CurrencyCreateSerializer,
    GameLevelSerializer,
)
from apps.courts.models import Court
from apps.courts.serializers import CourtCreateSerializer
from apps.event.models import Game, Tourney
from apps.event.serializers import GameCreateSerializer
from apps.locations.models import City, Country
from apps.locations.serializers import (
    CityCreateSerializer,
    CountryCreateSerializer,
)
from apps.players.models import Player

logger = logging.getLogger(__name__)


class FileUploadService:
    """
    Service for processing uploaded files.
    Supports JSON file type for loading model data.
    Implements singleton pattern.
    attrs:
        _model_mapping_class (Dict[str, Any]): Mapping of model names to their
            handlers.
        _model_processing_order (tuple[str]): Order in which models should be
            processed.
        _private_models_mapping_class (Dict[str, Any]): Mapping for private
            models only accessible in debug mode.
        max_file_size (int): Maximum allowed file size for upload.
        _supported_file_types (tuple[str]): Supported file types for upload.
        _extended_model_access (bool): Enable extended model processing.
    """

    def __new__(cls):
        """Singleton pattern implementation."""
        if not hasattr(cls, 'instance'):
            cls.instance = super(FileUploadService, cls).__new__(cls)
        return cls.instance

    def __init__(self):
        """Initialize model mapping for file processing."""
        self._model_mapping_class = {
            'countries': CountryModelMapping(),
            'cities': CityModelMapping(),
            'courts': CourtModelMapping(),
            'currencies': CurrencyTypeModelMapping(),
            'levels': LevelsModelMapping(),
        }
        self._private_models_mapping_class = {
            'players': PlayerModelMapping(),
            'games': GameModelMapping(),
            'tourneys': TourneyModelMapping(),
        }
        self._model_processing_order: tuple[str] = (
            'levels',
            'countries',
            'cities',
            'currencies',
            'courts',
        )
        self._supported_file_types: tuple[str] = SUPPORTED_FILE_TYPES
        self.max_file_size: int = MAX_FILE_SIZE
        self._extended_model_access: bool = settings.DEBUG

    @property
    def model_mapping_class(self) -> Dict[str, Any]:
        if self._extended_model_access:
            return {
                **self._model_mapping_class,
                **self._private_models_mapping_class,
            }
        return self._model_mapping_class

    @property
    def model_processing_order(self) -> tuple[str]:
        if self._extended_model_access:
            return self._model_processing_order + tuple(
                self._private_models_mapping_class.keys()
            )
        return self._model_processing_order

    @property
    def private_models_mapping_class(self) -> Dict[str, Any]:
        return self._private_models_mapping_class

    @property
    def supported_file_types(self) -> tuple[str]:
        return self._supported_file_types

    def detect_file_type(self, file) -> str:
        """Automatically detect file type."""
        filename = file.name.lower()
        if filename.endswith('.json'):
            return 'json'
        if filename.endswith('.csv'):
            return 'csv'
        if filename.endswith('.xlsx') or filename.endswith('.xls'):
            return 'excel'
        return filename.split('.')[-1]

    def process_file(self, file) -> Dict[str, Any]:
        """Process file based on its type."""
        file_type = self.detect_file_type(file)
        if file_type == 'json':
            return self.proccess_json_load(file)
        if file_type == 'excel':
            return self._process_excel_file(file)
        return {
            'success': False,
            'messages': ['Unsupported file type {file_type}'],
        }

    def download_file_by_path(self, file_path: str) -> bytes:
        """Download file from given path."""
        if not os.path.exists(file_path):
            raise FileNotFoundError(f'file not found at {file_path}')
        with open(file_path, 'r', encoding='utf-8') as f:
            return f.read()

    def proccess_json_load(
        self,
        file,
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
            messages = []
            for model_name in self.model_processing_order:
                if model_name in data and data[model_name]:
                    if self.model_mapping_class[model_name].serializer is None:
                        m = f'Skipped - {model_name} with no serializer'
                        if model_name in self.private_models_mapping_class:
                            m = (
                                f'Skipped - {model_name} private model'
                                'in production mode'
                            )
                        logger.warning(m)
                        messages.append(m)
                        continue
                    result = self._process_model_data(
                        model_name,
                        data[model_name],
                    )
                    messages.extend(result['messages'])
            return {
                'success': any('created' in msg.lower() for msg in messages),
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
    ) -> Dict[str, Any]:
        """Process data for specific model using serializer validation."""
        mapping_class: BaseModelMapping = self.model_mapping_class[model_name]
        messages = []
        for obj_data in model_data:
            serializer = mapping_class.serializer(data=obj_data)
            logger.info(f'Validating {model_name}: {obj_data}')
            if serializer.is_valid():
                try:
                    serializer.save()
                    status = 'created'
                    messages.append(f'{status} - {model_name}: {obj_data}')
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
                    f'error - {model_name}: {obj_data} - {error_str}'
                )
        return {'success': True, 'messages': messages}

    def _process_excel_file(
        self,
        file,
    ) -> dict:
        """
        Process Excel file with model data.
        Checks for correct model mapping and required fields.
        Then processes data using serializers.
        Turn execel data into list of dicts and call _process_model_data.
        """
        filename = os.path.splitext(file.name)[0].lower()
        mapping_class = self.model_mapping_class.get(filename)
        if not mapping_class:
            if filename in self.private_models_mapping_class:
                return {
                    'success': False,
                    'messages': [
                        f'Model {filename} upload is restricted in '
                        'production mode.',
                    ],
                }
            return {
                'success': False,
                'messages': [
                    f'Unknown model mapping for file: {filename}',
                ],
            }
        serializer_class = mapping_class.serializer
        if serializer_class is None:
            return {
                'success': False,
                'messages': [
                    f'No serializer for model: {filename}',
                ],
            }
        wb = openpyxl.load_workbook(file)
        ws = wb.active
        headers = [
            cell.value for cell in next(ws.iter_rows(min_row=1, max_row=1))
        ]
        excel_fields = set(headers)
        expected_fields = set(mapping_class.expected_fields)
        if excel_fields != expected_fields:
            missing = expected_fields - excel_fields
            print(excel_fields, expected_fields)
            return {
                'success': False,
                'messages': [f'Missing model fields: {missing}'],
            }
        model_data = []
        for row in ws.iter_rows(min_row=2, values_only=True):
            obj_data = dict(zip(headers, row, strict=False))
            if filename == 'courts':
                location_keys = [
                    'longitude',
                    'latitude',
                    'court_name',
                    'country',
                    'city',
                ]
                location_data = {
                    k: obj_data.pop(k) for k in location_keys if k in obj_data
                }
                obj_data['location'] = location_data
            if filename == 'games' and isinstance(obj_data.get('levels'), str):
                obj_data['levels'] = [
                    v.strip()
                    for v in obj_data['levels'].split(',')
                    if v.strip()
                ]
            model_data.append(obj_data)
        return self._process_model_data(filename, model_data)

    def summarize_results(self, result: dict) -> dict:
        """Summarize results by counting created, and error messages."""
        messages = result.get('messages', [])
        summary = {'created': 0, 'errors': 0}
        for msg in messages:
            msg_lower = msg.lower()
            if 'created' in msg_lower:
                summary['created'] += 1
            elif 'error' in msg_lower:
                summary['errors'] += 1
        summary_messages = [
            f'Created: {summary["created"]} db objects',
            f'Errors(skipped): {summary["errors"]}',
        ]
        result['messages'] = summary_messages
        return result


class BaseModelMapping:
    """
    Base class for model mapping.
    Subclasses must set self.model, self.serializer, self.can_update.
    """

    def __init__(self):
        self._model = None
        self._serializer = None
        self._name = ''
        self._expected_xlsx_fields = ()

    @property
    def model(self):
        return self._model

    @property
    def serializer(self):
        return self._serializer

    @property
    def name(self):
        return self._name

    @property
    def expected_fields(self):
        return self._expected_xlsx_fields

    def get_serializer_fields(self) -> List[str]:
        """Get non-read-only fields from the serializer."""

        if not self.serializer:
            return []
        return tuple(
            name
            for name, field in self._serializer().get_fields().items()
            if not field.read_only
        )


class CountryModelMapping(BaseModelMapping):
    """Model mapping for Country."""

    def __init__(self):
        self._name = 'countries'
        self._model = Country
        self._serializer = CountryCreateSerializer
        self._expected_xlsx_fields = self.get_serializer_fields()


class CityModelMapping(BaseModelMapping):
    """Model mapping for City."""

    def __init__(self):
        self._name = 'cities'
        self._model = City
        self._serializer = CityCreateSerializer
        self._expected_xlsx_fields = self.get_serializer_fields()


class CourtModelMapping(BaseModelMapping):
    """Model mapping for Court."""

    def __init__(self):
        self._name = 'courts'
        self._model = Court
        self._serializer = CourtCreateSerializer
        self._expected_xlsx_fields = (
            'longitude',
            'latitude',
            'country',
            'city',
            'court_name',
            'description',
            'working_hours',
            'price_description',
        )


class PlayerModelMapping(BaseModelMapping):
    """Model mapping for Player."""

    def __init__(self):
        self._name = 'players'
        self._model = Player
        self._serializer = None
        self._expected_xlsx_fields = None


class GameModelMapping(BaseModelMapping):
    """Model mapping for Game."""

    def __init__(self):
        self._name = 'games'
        self._model = Game
        self._serializer = GameCreateSerializer
        self._expected_xlsx_fields = self.get_serializer_fields()


class TourneyModelMapping(BaseModelMapping):
    """Model mapping for Tourney."""

    def __init__(self):
        self._name = 'tourneys'
        self._model = Tourney
        self._serializer = None
        self._expected_xlsx_fields = None


class CurrencyTypeModelMapping(BaseModelMapping):
    """Model mapping for CurrencyType."""

    def __init__(self):
        self._name = 'currencies'
        self._model = CurrencyType
        self._serializer = CurrencyCreateSerializer
        self._expected_xlsx_fields = self.get_serializer_fields()


class LevelsModelMapping(BaseModelMapping):
    """Model mapping for Levels."""

    def __init__(self):
        self._name = 'levels'
        self._model = GameLevel
        self._serializer = GameLevelSerializer
        self._expected_xlsx_fields = self.get_serializer_fields()
