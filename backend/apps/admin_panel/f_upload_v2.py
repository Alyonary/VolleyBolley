import logging
from typing import Any, Dict, List

from django.conf import settings

from apps.admin_panel.model_mappings import (
    MappingRegistry,
)
from apps.admin_panel.parsers import ExcelParser, JsonParser
from apps.core.base import BaseParser

logger = logging.getLogger(__name__)


class FileUploadServiceV2:
    def __init__(
        self, registry: MappingRegistry, parsers: Dict[str, BaseParser]
    ):
        self._registry = registry
        self._parsers = parsers
        self._processing_order = (
            'levels',
            'countries',
            'cities',
            'currencies',
            'courts',
            'players',
            'games',
            'tourneys',
        )

    def process_file(self, file) -> Dict[str, Any]:
        """Main entry point for file processing."""
        file_type = self._detect_type(file)
        parser = self._parsers.get(file_type)
        if not parser:
            return {
                'success': False,
                'messages': [f'Unsupported file type: {file_type}'],
            }
        try:
            parsed_data = parser.parse(file, self._registry)
            return self._execute_import(parsed_data)
        except Exception as e:
            logger.error(f'Processing error: {str(e)}')
            return {'success': False, 'messages': [str(e)]}

    def _execute_import(self, data: Dict[str, List[Dict]]) -> Dict[str, Any]:
        """Iterates through data in specific order and saves to DB."""
        messages = []
        available_mappings = self._registry.get_all()
        for model_name in self._processing_order:
            if model_name not in data or not data[model_name]:
                continue
            mapping = available_mappings.get(model_name)
            if not mapping or not mapping.serializer:
                continue
            for row_data in data[model_name]:
                result = self._save_row(
                    model_name, mapping.serializer, row_data
                )
                messages.append(result)
        return {
            'success': any('created' in m.lower() for m in messages),
            'messages': messages,
        }

    def _save_row(self, name: str, serializer_class: Any, data: Dict) -> str:
        """Validates and saves a single model instance."""
        serializer = serializer_class(data=data)
        if serializer.is_valid():
            serializer.save()
            return f'created - {name}: {data}'
        errors = '; '.join(
            [f'{f}: {", ".join(e)}' for f, e in serializer.errors.items()]
        )
        return f'error - {name}: {errors}'

    def _detect_type(self, file) -> str:
        name = file.name.lower()
        if name.endswith('.json'):
            return 'json'
        if name.endswith(('.xlsx', '.xls')):
            return 'excel'
        return 'unknown'

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
        return {'success': summary['created'] > 0, 'message': summary_messages}


def get_upload_service():
    """Factory to assemble the service with its dependencies."""
    registry = MappingRegistry(extended_model_access=settings.DEBUG)
    parsers = {
        'json': JsonParser(),
        'excel': ExcelParser(),
    }
    return FileUploadServiceV2(registry, parsers)
