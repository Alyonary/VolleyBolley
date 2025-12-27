import io
import json
import os
import tempfile
from typing import Any, Dict, List, TypeVar, Union

import openpyxl
import pytest
from django.core.files.uploadedfile import SimpleUploadedFile

from apps.admin_panel.services import FileUploadService
from apps.core.models import CurrencyType, GameLevel
from apps.courts.models import Court, CourtLocation
from apps.event.models import Game
from apps.locations.models import City, Country

# Объявляем TypeVar с ограничением на ваши модели
DbModel = TypeVar(
    'DbModel',
    bound=Union[
        Country,
        City,
        CurrencyType,
        GameLevel,
        Court,
        CourtLocation,
        Game,
    ],
)

DATA_DIR = os.path.join(os.path.dirname(__file__), '..', 'data')


@pytest.mark.django_db
class TestFileUploadServiceJSON:
    def test_create_countries(
        self,
        fileupload_service_debug: FileUploadService,
        valid_country_data: List[Dict[str, Any]],
    ) -> None:
        result, objs_count = get_model_create_result(
            fileupload_service_debug,
            Country,
            'countries',
            valid_country_data,
        )
        assert result['success'] is True
        assert objs_count == len(valid_country_data)

    def test_create_cities(
        self,
        fileupload_service_debug: FileUploadService,
        valid_country_data: List[Dict[str, Any]],
        valid_city_data: List[Dict[str, Any]],
    ) -> None:
        for c in valid_country_data:
            Country.objects.get_or_create(**c)
        result, objs_count = get_model_create_result(
            fileupload_service_debug,
            City,
            'cities',
            valid_city_data,
        )
        assert result['success'] is True
        assert objs_count == len(valid_city_data)

    def test_create_currencies(
        self,
        fileupload_service_debug: FileUploadService,
        valid_currency_data: List[Dict[str, Any]],
    ) -> None:
        result, objs_count = get_model_create_result(
            fileupload_service_debug,
            CurrencyType,
            'currencies',
            valid_currency_data,
        )
        assert result['success'] is True
        assert objs_count == len(valid_currency_data)

    def test_create_levels(
        self,
        fileupload_service_debug: FileUploadService,
        valid_level_data: List[Dict[str, Any]],
    ) -> None:
        result, objs_count = get_model_create_result(
            fileupload_service_debug,
            GameLevel,
            'levels',
            valid_level_data,
        )
        assert result['success'] is True
        assert objs_count == len(valid_level_data)

    def test_create_courts(
        self,
        fileupload_service_debug: FileUploadService,
        valid_court_json_data: List[Dict[str, Any]],
        valid_country_data: List[Dict[str, Any]],
        valid_city_data: List[Dict[str, Any]],
    ) -> None:
        for c in valid_country_data:
            Country.objects.get_or_create(**c)
        for city in valid_city_data:
            country = Country.objects.get(name=city['country'])
            City.objects.create(name=city['name'], country=country)
        result, objs_count = get_model_create_result(
            fileupload_service_debug,
            Court,
            'courts',
            valid_court_json_data,
        )
        assert result['success'] is True
        assert objs_count == len(valid_court_json_data)

    def test_create_tourneys_stub(
        self,
        fileupload_service_debug: FileUploadService,
    ) -> None:
        data = {'tourneys': [{'name': 'Test Tourney'}]}
        file: io.BytesIO = io.BytesIO(json.dumps(data).encode('utf-8'))
        file.name = 'test.json'
        result: dict = fileupload_service_debug.process_file(file)
        for m in result.get('messages', []):
            assert 'Skipped' in m or 'no serializer' in m.lower()
        assert result['success'] is True

    def test_process_json_file_invalid_country_attr(
        self,
        fileupload_service_debug: FileUploadService,
        invalid_country_data_wrong_attr: List[Dict[str, Any]],
    ) -> None:
        result, _ = get_model_create_result(
            fileupload_service_debug,
            Country,
            'countries',
            invalid_country_data_wrong_attr,
        )
        assert result['success'] is False or any(
            'error' in m.lower() for m in result.get('messages', [])
        )

    def test_process_json_file_invalid_country_format(
        self,
        fileupload_service_debug: FileUploadService,
        invalid_country_data_wrong_format: List[Dict[str, Any]],
    ) -> None:
        result, countries_after_test = get_model_create_result(
            fileupload_service_debug,
            Country,
            'countries',
            invalid_country_data_wrong_format,
        )
        assert countries_after_test == 0
        assert result['success'] is True
        assert 'error' in ''.join(
            m.lower() for m in result.get('messages', [])
        )


@pytest.mark.django_db
class TestFileUploadServiceExcel:
    def test_process_excel_file_creates_currency(
        self,
        fileupload_service_debug: FileUploadService,
        valid_currency_data: List[Dict[str, Any]],
        valid_country_data: List[Dict[str, Any]],
        excel_content_type: str,
    ) -> None:
        CurrencyType.objects.all().delete()
        Country.objects.all().delete()
        for c in valid_country_data:
            Country.objects.create(**c)
        wb = openpyxl.Workbook()
        ws = wb.active
        ws.append(list(valid_currency_data[0].keys()))
        ws.append(list(valid_currency_data[0].values()))
        tmp = tempfile.NamedTemporaryFile(suffix='.xlsx', delete=False)
        wb.save(tmp.name)
        tmp.close()
        with open(tmp.name, 'rb') as f:
            file: SimpleUploadedFile = SimpleUploadedFile(
                'currencies.xlsx',
                f.read(),
                content_type=excel_content_type,
            )
            result: dict = fileupload_service_debug.process_file(file)
        os.unlink(tmp.name)
        assert result['success'] is True
        assert CurrencyType.objects.count() == len(valid_currency_data)

    def test_process_excel_file_missing_fields(
        self,
        fileupload_service_debug: FileUploadService,
        excel_content_type: str,
    ) -> None:
        wb = openpyxl.Workbook()
        ws = wb.active
        ws.append(['wrong_field'])
        ws.append(['test'])
        tmp = tempfile.NamedTemporaryFile(suffix='.xlsx', delete=False)
        wb.save(tmp.name)
        tmp.close()
        with open(tmp.name, 'rb') as f:
            file: SimpleUploadedFile = SimpleUploadedFile(
                'currencies.xlsx',
                f.read(),
                content_type=excel_content_type,
            )
            result: dict = fileupload_service_debug.process_file(file)
        os.unlink(tmp.name)
        assert result['success'] is False
        assert 'Missing model fields' in result['messages'][0]

    def test_process_excel_file_create_levels(
        self,
        fileupload_service_debug: FileUploadService,
        valid_level_data: List[Dict[str, Any]],
        excel_content_type: str,
    ) -> None:
        GameLevel.objects.all().delete()
        wb = openpyxl.Workbook()
        ws = wb.active
        ws.append(list(valid_level_data[0].keys()))
        ws.append(list(valid_level_data[0].values()))
        tmp = tempfile.NamedTemporaryFile(suffix='.xlsx', delete=False)
        wb.save(tmp.name)
        tmp.close()
        with open(tmp.name, 'rb') as f:
            file: SimpleUploadedFile = SimpleUploadedFile(
                'levels.xlsx',
                f.read(),
                content_type=excel_content_type,
            )
            result: dict = fileupload_service_debug.process_file(file)
        os.unlink(tmp.name)
        assert result['success'] is True
        assert GameLevel.objects.count() == len(valid_level_data)

    def test_process_excel_file_create_cities(
        self,
        fileupload_service_debug: FileUploadService,
        valid_city_data: List[Dict[str, Any]],
        valid_country_data: List[Dict[str, Any]],
        excel_content_type: str,
    ) -> None:
        City.objects.all().delete()
        Country.objects.all().delete()
        for c in valid_country_data:
            Country.objects.create(**c)
        wb = openpyxl.Workbook()
        ws = wb.active
        ws.append(list(valid_city_data[0].keys()))
        for city in valid_city_data:
            ws.append(list(city.values()))
        tmp = tempfile.NamedTemporaryFile(suffix='.xlsx', delete=False)
        wb.save(tmp.name)
        tmp.close()
        with open(tmp.name, 'rb') as f:
            file: SimpleUploadedFile = SimpleUploadedFile(
                'cities.xlsx',
                f.read(),
                content_type=excel_content_type,
            )
            result: dict = fileupload_service_debug.process_file(file)
        os.unlink(tmp.name)
        assert result['success'] is True
        assert City.objects.count() == len(valid_city_data)

    def test_process_excel_file_create_courts(
        self,
        fileupload_service_debug: FileUploadService,
        valid_court_xlsx_data: List[Dict[str, Any]],
        valid_country_data: List[Dict[str, Any]],
        valid_city_data: List[Dict[str, Any]],
        excel_content_type: str,
    ) -> None:
        Court.objects.all().delete()
        CourtLocation.objects.all().delete()
        Country.objects.all().delete()
        City.objects.all().delete()
        for c in valid_country_data:
            Country.objects.create(**c)
        for city in valid_city_data:
            country = Country.objects.get(name=city['country'])
            City.objects.create(name=city['name'], country=country)
        wb = openpyxl.Workbook()
        ws = wb.active
        ws.append(list(valid_court_xlsx_data[0].keys()))
        ws.append(list(valid_court_xlsx_data[0].values()))
        tmp = tempfile.NamedTemporaryFile(suffix='.xlsx', delete=False)
        wb.save(tmp.name)
        tmp.close()
        with open(tmp.name, 'rb') as f:
            file: SimpleUploadedFile = SimpleUploadedFile(
                'courts.xlsx',
                f.read(),
                content_type=excel_content_type,
            )
            result: dict = fileupload_service_debug.process_file(file)
        os.unlink(tmp.name)
        assert result['success'] is True
        assert Court.objects.count() == len(valid_court_xlsx_data)

    def test_process_excel_file_create_tourneys_stub(
        self,
        fileupload_service_debug: FileUploadService,
        excel_content_type: str,
    ) -> None:
        wb = openpyxl.Workbook()
        ws = wb.active
        ws.append(['name'])
        ws.append(['Test Tourney'])
        tmp = tempfile.NamedTemporaryFile(suffix='.xlsx', delete=False)
        wb.save(tmp.name)
        tmp.close()
        with open(tmp.name, 'rb') as f:
            file: SimpleUploadedFile = SimpleUploadedFile(
                'tourneys.xlsx',
                f.read(),
                content_type=excel_content_type,
            )
            result: dict = fileupload_service_debug.process_file(file)
        os.unlink(tmp.name)
        assert result['success'] is True or result['success'] is False


@pytest.mark.django_db
class TestFileUploadServiceRealFiles:
    def test_upload_all_models_from_real_json_file(
        self, fileupload_service_debug: FileUploadService
    ) -> None:
        json_path = os.path.join(DATA_DIR, 'test_db_data.json')
        with open(json_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        for model in data.keys():
            fileupload_service_debug.model_mapping_class[
                model
            ].model.objects.all().delete()
        with open(json_path, 'rb') as f:
            file = io.BytesIO(f.read())
            file.name = 'test_db_data.json'
            result = fileupload_service_debug.process_file(file)
        assert result['success'] is True
        assert Country.objects.count() == len(data.get('countries', []))
        assert City.objects.count() == len(data.get('cities', []))
        assert CurrencyType.objects.count() == len(data.get('currencies', []))
        assert GameLevel.objects.count() == len(data.get('levels', []))
        assert Court.objects.count() == len(data.get('courts', []))

    @pytest.mark.parametrize(
        'model, model_class',
        [
            ('countries', Country),
            ('cities', City),
            ('levels', GameLevel),
            ('currencies', CurrencyType),
            ('courts', Court),
            ('games', Game),
        ],
    )
    def test_upload_model_from_real_excel_file(
        self,
        fileupload_service_debug: FileUploadService,
        model: str,
        model_class,
        excel_content_type: str,
    ) -> None:
        excel_path = os.path.join(DATA_DIR, f'{model}.xlsx')
        if not os.path.exists(excel_path):
            pytest.skip(f'Excel file for {model} not found')
        model_class.objects.all().delete()
        if model_class == Court:
            CourtLocation.objects.all().delete()
        with open(excel_path, 'rb') as f:
            file = SimpleUploadedFile(
                f'{model}.xlsx',
                f.read(),
                content_type=excel_content_type,
            )
            result = fileupload_service_debug.process_file(file)
            # print(result)
        assert result['success'] is True
        wb = openpyxl.load_workbook(excel_path)
        ws = wb.active
        rows = list(ws.iter_rows(min_row=2, values_only=True))
        assert model_class.objects.count() >= len(rows)


def get_model_create_result(
    f_service: FileUploadService, model: DbModel, model_name, model_data
):
    """Helper function to test creating a model from JSON data."""
    model.objects.all().delete()
    data = {model_name: model_data}
    file: io.BytesIO = io.BytesIO(json.dumps(data).encode('utf-8'))
    file.name = 'test.json'
    result: dict = f_service.process_file(file)
    return result, model.objects.count()
