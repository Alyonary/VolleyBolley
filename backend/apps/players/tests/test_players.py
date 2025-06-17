import pytest
from django.contrib.auth import get_user_model
from rest_framework import status
from rest_framework.test import APIClient

from apps.users.models import Location

User = get_user_model()
PLAYERS_URL = '/api/players/'


@pytest.fixture
def api_client():
    """Создание API клиента для выполнения запросов."""
    return APIClient()


@pytest.fixture
def players(db):
    """
    Создание тестовых пользователей.

    В системе будет 4 пользователя:
    - 2 начинающих игрока в стране CY
    - 1 начинающий игрок в стране TH
    - 1 продвинутый игрок в стране TH
    """

    cyprus = Location.objects.create(country='CY', city='Nicosia')
    thailand = Location.objects.create(country='TH', city='Bangkok')

    def create_user(username, level, location, phone='+70000000000'):
        """Создание пользователя с заданными параметрами."""
        return User.objects.create_user(
            username=username,
            password='pass',
            phone_number=phone,
            game_skill_level=level,
            location=location,
        )

    create_user(
        'beginner_cyprus_1',
        User.GameSkillLevel.BEGINNER,
        cyprus,
        '+70000000001',
    )
    create_user(
        'beginner_cyprus_2',
        User.GameSkillLevel.BEGINNER,
        cyprus,
        '+70000000002',
    )
    create_user(
        'beginner_thailand_1',
        User.GameSkillLevel.BEGINNER,
        thailand,
        '+17000000003',
    )
    create_user(
        'advanced_thailand_2',
        User.GameSkillLevel.ADVANCED,
        thailand,
        '+17000000004',
    )


@pytest.mark.django_db
def test_filter_by_level(api_client, players):
    """Проверка фильтрации по уровню навыков игрока."""
    resp = api_client.get(PLAYERS_URL, {'level': 'beginner'})

    assert resp.status_code == status.HTTP_200_OK

    objs = resp.json()

    assert {u['username'] for u in objs} == {
        'beginner_cyprus_1',
        'beginner_cyprus_2',
        'beginner_thailand_1',
    }


@pytest.mark.django_db
def test_filter_by_country(api_client, players):
    """Проверка фильтрации по стране."""
    resp = api_client.get(PLAYERS_URL, {'country': 'CY'})

    assert resp.status_code == status.HTTP_200_OK
    objs = resp.json()

    assert {u['username'] for u in objs} == {
        'beginner_cyprus_1',
        'beginner_cyprus_2',
    }


@pytest.mark.django_db
def test_filter_by_both_fields(api_client, players):
    """Проверка фильтрации по уровню навыков и стране одновременно."""
    resp = api_client.get(PLAYERS_URL, {'level': 'advanced', 'country': 'TH'})

    assert resp.status_code == status.HTTP_200_OK
    objs = resp.json()

    assert {u['username'] for u in objs} == {'advanced_thailand_2'}
