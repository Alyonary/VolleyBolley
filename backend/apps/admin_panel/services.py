import json
import logging
import os
from typing import Any, Dict, List

import openpyxl
from django.conf import settings

from apps.courts.models import Court
from apps.courts.serializers import CourtCreateSerializer
from apps.event.models import Game, Tourney
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
        }
        self._model_processing_order: tuple[str] = (
            'countries',
            'cities',
            'courts',
        )
        self._supported_file_types: tuple[str] = ('json', 'excel')
        self.max_file_size: int = 10 * 1024 * 1024  # 10 MB
        self._extended_model_access: bool = settings.DEBUG

    @property
    def model_mapping_class(self) -> Dict[str, Any]:
        return self._model_mapping_class

    @property
    def model_processing_order(self) -> tuple[str]:
        if self._extended_model_access:
            return self._model_processing_order + (
                'players',
                'games',
                'tourneys',
            )
        return self._model_processing_order

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
            'messages': 'Unsupported file type {file_type}',
        }

    def download_file_by_path(self, file_path: str) -> bytes:
        """Download file from given path."""
        if not os.path.exists(file_path):
            raise FileNotFoundError(f'FAQ file not found at {file_path}')
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
                    result = self._process_model_data(
                        model_name,
                        data[model_name],
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
            model_data.append(obj_data)
        return self._process_model_data(filename, model_data)


class BaseModelMapping:
    """
    Base class for model mapping.
    Subclasses must set self.model, self.serializer, self.can_update.
    """

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


class CountryModelMapping(BaseModelMapping):
    """Model mapping for Country."""

    def __init__(self):
        self._name = 'countries'
        self._model = Country
        self._serializer = CountryCreateSerializer
        self._expected_xlsx_fields = ('name',)


class CityModelMapping(BaseModelMapping):
    """Model mapping for City."""

    def __init__(self):
        self._name = 'cities'
        self._model = City
        self._serializer = CityCreateSerializer
        self._expected_xlsx_fields = ('name', 'country')


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
        self.__expected_xlsx_fields = None


class GameModelMapping(BaseModelMapping):
    """Model mapping for Game."""

    def __init__(self):
        self._name = 'games'
        self._model = Game
        self._serializer = None
        self._expected_xlsx_fields = None


class TourneyModelMapping(BaseModelMapping):
    """Model mapping for Tourney."""

    def __init__(self):
        self._name = 'tourneys'
        self._model = Tourney
        self._serializer = None
        self._expected_xlsx_fields = None
