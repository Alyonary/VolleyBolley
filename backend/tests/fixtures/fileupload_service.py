from typing import Any, Dict, List

import pytest


@pytest.fixture
def excel_content_type() -> str:
    return 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'


@pytest.fixture
def valid_country_data() -> List[Dict[str, str]]:
    return [
        {'name': 'Thailand'},
        {'name': 'Cyprus'},
    ]


@pytest.fixture
def invalid_country_data_wrong_attr() -> List[Dict[str, Any]]:
    return [{'title': 'Thailand'}]


@pytest.fixture
def invalid_country_data_wrong_format() -> List[Dict[str, Any]]:
    return [{'name': 2}]


@pytest.fixture
def valid_city_data() -> List[Dict[str, str]]:
    return [
        {'name': 'Bangkok', 'country': 'Thailand'},
        {'name': 'Nicosia', 'country': 'Cyprus'},
    ]


@pytest.fixture
def invalid_city_data_wrong_attr() -> List[Dict[str, Any]]:
    return [{'city_name': 'Bangkok'}]


@pytest.fixture
def invalid_city_data_wrong_format() -> List[Dict[str, Any]]:
    return [{'name': 'Bangkok', 'country': 'invalid_name'}]


@pytest.fixture
def valid_currency_data() -> List[Dict[str, str]]:
    return [
        {'currency_type': 'THB', 'currency_name': '฿', 'country': 'Thailand'},
    ]


@pytest.fixture
def invalid_currency_data_wrong_attr() -> List[Dict[str, Any]]:
    return [{'type': 'THB', 'symbol': '฿'}]


@pytest.fixture
def invalid_currency_data_wrong_format() -> List[Dict[str, Any]]:
    return [{'currency_type': 100, 'currency_name': 200}]


@pytest.fixture
def valid_level_data() -> List[Dict[str, str]]:
    return [{'name': 'PRO'}]


@pytest.fixture
def invalid_level_data_wrong_attr() -> List[Dict[str, Any]]:
    return [{'level': 'PRO'}]


@pytest.fixture
def invalid_level_data_wrong_format() -> List[Dict[str, Any]]:
    return [{'name': 12345}]


@pytest.fixture
def valid_court_json_data() -> List[Dict[str, Any]]:
    return [
        {
            'location': {
                'longitude': 100.5018,
                'latitude': 13.7563,
                'country': 'Thailand',
                'city': 'Bangkok',
                'court_name': 'Bangkok Arena',
            },
            'description': 'Main arena in Bangkok',
            'working_hours': '08:00-22:00',
            'price_description': 'Premium',
            'tags': 'outdoor,premium,arena,1 courts',
            'contact_type': 'PHONE',
            'contact': '79553631234',
        }
    ]


@pytest.fixture
def valid_court_xlsx_data() -> List[Dict[str, Any]]:
    return [
        {
            'longitude': 100.5018,
            'latitude': 13.7563,
            'country': 'Thailand',
            'city': 'Bangkok',
            'court_name': 'Bangkok Arena',
            'description': 'Main arena in Bangkok',
            'working_hours': '08:00-22:00',
            'price_description': 'Premium',
            'tags': 'outdoor,premium,arena,1 courts',
            'contact_type': 'PHONE',
            'contact': '79553631234',
        }
    ]


@pytest.fixture
def invalid_court_data_wrong_attr() -> List[Dict[str, Any]]:
    return [
        {
            'lng': 100.5018,
            'lat': 13.7563,
            'nation': 1,
            'town': 1,
            'name': 'Bangkok Arena',
        }
    ]


@pytest.fixture
def invalid_court_data_wrong_format() -> List[Dict[str, Any]]:
    return [
        {
            'longitude': 'not_a_float',
            'latitude': None,
            'country': 'not_an_id',
            'city': 'not_an_id',
            'court_name': 123,
            'description': 456,
            'working_hours': 789,
            'price_description': 0.5,
            'tags': 123,
            'contact_type': True,
            'contact': False,
        }
    ]


@pytest.fixture
def json_models_data() -> Dict[str, Any]:
    return {
        'games': [],
        'tourneys': [],
        'players': [],
    }
