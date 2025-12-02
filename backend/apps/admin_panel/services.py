import json
import logging
import os
from typing import Any, Dict, List

from django.conf import settings
from django.contrib.auth import get_user_model

from apps.courts.models import Court, CourtLocation
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
            'locations': CourtLocationModelMapping(),
            'courts': CourtModelMapping(),
        }
        self._model_processing_order: tuple[str] = (
            'countries',
            'cities',
            'locations',
            'courts',
        )
        self._supported_file_types: tuple[str] = ('json',)
        self._extended_model_access: bool = settings.DEBUG

    @property
    def model_mapping_class(self) -> Dict[str, Any]:
        return self._model_mapping_class

    @property
    def model_processing_order(self) -> tuple[str]:
        if self._extended_model_access:
            return self._model_processing_order + (
                'users',
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
        return None

    def process_file(self, file, need_update: bool = False) -> Dict[str, Any]:
        """Process file based on its type."""
        file_type = self.detect_file_type(file)
        if file_type not in self.supported_file_types:
            message = f'Download failed. Unsupported file type: {file_type}.'
            return {'success': False, 'error': message}
        if file_type == 'json':
            return self.proccess_json_load(file, need_update)
        return None

    def download_file_by_path(self, file_path: str) -> bytes:
        """Download file from given path."""
        if not os.path.exists(file_path):
            raise FileNotFoundError(f'FAQ file not found at {file_path}')
        with open(file_path, 'r', encoding='utf-8') as f:
            return f.read()

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
            messages = []
            for model_name in self.model_processing_order:
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
        if model_name not in self.model_mapping_class:
            return {'messages': [f'{model_name}: Unknown model']}
        mapping_class: BaseModelMapping = self.model_mapping_class[model_name]
        messages = []
        for obj_data in model_data:
            serializer = mapping_class.serializer(data=obj_data)
            logger.info(f'Validating {model_name}: {obj_data}')
            if serializer.is_valid():
                validated_data = serializer.validated_data
                try:
                    obj, created = mapping_class.model.objects.get_or_create(
                        **validated_data
                    )
                    if (
                        not created
                        and need_update
                        and mapping_class.can_update
                    ):
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
    def can_update(self):
        return self._can_update


class CountryModelMapping(BaseModelMapping):
    """Model mapping for Country."""

    def __init__(self):
        self._model = Country
        self._serializer = CountryCreateSerializer
        self._can_update = False


class CityModelMapping(BaseModelMapping):
    """Model mapping for City."""

    def __init__(self):
        self._model = City
        self._serializer = CityCreateSerializer
        self._can_update = False


class CourtLocationModelMapping(BaseModelMapping):
    """Model mapping for CourtLocation."""

    def __init__(self):
        self._model = CourtLocation
        self._serializer = None
        self._can_update = True


class CourtModelMapping(BaseModelMapping):
    """Model mapping for Court."""

    def __init__(self):
        self._model = Court
        self._serializer = None
        self._can_update = True


class UserModelMapping(BaseModelMapping):
    """Model mapping for User."""

    def __init__(self):
        self._model = get_user_model()
        self._serializer = None
        self._can_update = True


class PlayerModelMapping(BaseModelMapping):
    """Model mapping for Player."""

    def __init__(self):
        self._model = Player
        self._serializer = None
        self._can_update = True


class GameModelMapping(BaseModelMapping):
    """Model mapping for Game."""

    def __init__(self):
        self._model = Game
        self._serializer = None
        self._can_update = True


class TourneyModelMapping(BaseModelMapping):
    """Model mapping for Tourney."""

    def __init__(self):
        self._model = Tourney
        self._serializer = None
        self._can_update = True
