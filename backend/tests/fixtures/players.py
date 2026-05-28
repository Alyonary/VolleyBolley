from typing import Any, Dict, List

import pytest

from apps.players.models import Player
from apps.users.models import User


@pytest.fixture
def player_data(active_user: User) -> Dict[str, Any]:
    """Return initial registration data for a player."""
    return {
        'user': active_user,
        'gender': 'MALE',
        'level': 'LIGHT',
        'is_registered': True,
    }


@pytest.fixture
def player_updated_data(countries_cities: Dict[str, Any]) -> Dict[str, Any]:
    """Return full update profile details for a player."""
    paphos = countries_cities['Cyprus'].cities.filter(name='Paphos').first()
    return {
        'first_name': 'UpdatedName',
        'last_name': 'UpdatedLastName',
        'country': countries_cities['Cyprus'].id,
        'city': paphos.id if paphos else None,
        'date_of_birth': '1995-05-05',
        'gender': 'MALE',
        'avatar': 'fake-base64-str',
        'level': 'PRO',
        'is_registered': False,
    }


@pytest.fixture
def player_partial_updated_data() -> Dict[str, str]:
    """Return partial parameters for a profile update."""
    return {
        'last_name': 'PartialUpdateLastName',
        'date_of_birth': '1995-05-05',
    }


@pytest.fixture
def player_generated_after_login_data(
    user_generated_after_login: User,
) -> Dict[str, Any]:
    """Return mock representation profiles generated post login."""
    player = user_generated_after_login.player
    return {
        'first_name': user_generated_after_login.first_name,
        'last_name': user_generated_after_login.last_name,
        'date_of_birth': player.date_of_birth,
        'country': None,
        'city': None,
        'gender': player.gender,
        'avatar': player.avatar,
        'level': player.rating.grade,
        'is_registered': player.is_registered,
    }


@pytest.fixture
def registered_player_data(
    user_with_registered_player: User,
) -> Dict[str, Any]:
    """Return details from an already registered user profile."""
    player = user_with_registered_player.player
    return {
        'first_name': user_with_registered_player.first_name,
        'last_name': user_with_registered_player.last_name,
        'date_of_birth': player.date_of_birth,
        'country': player.country.id,
        'city': player.city.id,
        'gender': player.gender,
        'avatar': player.avatar,
        'level': player.rating.grade,
        'is_registered': player.is_registered,
    }


@pytest.fixture
def bulk_create_not_registered_players(
    bulk_create_users: List[User],
) -> List[Player]:
    """Generate a sequence of unregistered profiles for testing."""
    players: List[Player] = []
    for user in bulk_create_users:
        player, _ = Player.objects.get_or_create(user=user)
        player.is_registered = False
        player.save()
        players.append(player)
    return players


@pytest.fixture
def bulk_create_registered_players(
    bulk_create_users: List[User], countries_cities: Dict[str, Any]
) -> List[Player]:
    """Generate registered user profiles split by geography."""
    players: List[Player] = []
    cyprus = countries_cities['Cyprus']
    paphos = cyprus.cities.filter(name='Paphos').first()
    thailand = countries_cities['Thailand']
    bangkok = thailand.cities.filter(name='Bangkok').first()

    for user in bulk_create_users[:2]:
        player, _ = Player.objects.get_or_create(user=user)
        player.is_registered = True
        player.country = cyprus
        player.city = paphos
        player.save()
        players.append(player)

    for user in bulk_create_users[2:]:
        player, _ = Player.objects.get_or_create(user=user)
        player.is_registered = True
        player.country = thailand
        player.city = bangkok
        player.save()
        players.append(player)

    return players


@pytest.fixture
def player_male_light(player_data: Dict[str, Any]) -> Player:
    """Instantiate a real player record with light ranking."""
    grade = player_data.pop('level')
    player = Player.objects.create(**player_data)
    rating = player.rating
    rating.grade = grade
    rating.save()
    return player


@pytest.fixture
def player_data_for_registration(
    countries_cities: Dict[str, Any],
) -> Dict[str, Any]:
    """Return standard form profile submission payloads."""
    bangkok = (
        countries_cities['Thailand'].cities.filter(name='Bangkok').first()
    )
    return {
        'first_name': 'RegisterPlayerName',
        'last_name': 'RegisterPlayerSurname',
        'gender': 'FEMALE',
        'level': 'MEDIUM',
        'date_of_birth': '1990-06-06',
        'country': countries_cities['Thailand'].id,
        'city': bangkok.id if bangkok else None,
        'avatar': 'registered-player-fake-avatar',
        'is_registered': False,
    }


@pytest.fixture
def player_no_data_for_registration() -> Dict[str, Any]:
    """Return empty mapping dictionary payload representation."""
    return {}


@pytest.fixture
def player_necessary_data_for_registration(
    countries_cities: Dict[str, Any],
) -> Dict[str, Any]:
    """Return essential payload mappings avoiding options values."""
    bangkok = (
        countries_cities['Thailand'].cities.filter(name='Bangkok').first()
    )
    return {
        'first_name': 'Name',
        'last_name': 'LastName',
        'country': countries_cities['Thailand'].id,
        'city': bangkok.id if bangkok else None,
        'level': 'MEDIUM',
        'date_of_birth': '1990-06-06',
        'gender': 'FEMALE',
    }


@pytest.fixture
def player_not_default_data(
    countries_cities: Dict[str, Any], active_user: User
) -> Dict[str, Any]:
    """Provide parameters for non default registration mock setups."""
    bangkok = (
        countries_cities['Thailand'].cities.filter(name='Bangkok').first()
    )
    return {
        'user': active_user,
        'gender': 'FEMALE',
        'date_of_birth': '2000-01-01',
        'country': countries_cities['Thailand'],
        'city': bangkok,
    }


@pytest.fixture
def player_grade() -> str:
    """Return constant grade indicator tag string."""
    return 'PRO'


@pytest.fixture
def player_no_geo() -> Player:
    """Generate a custom record completely detached from geo settings."""
    user = User.objects.create_user(
        username='no_geo_user', password='password123'
    )
    player = Player.objects.create(
        user=user,
        gender='FEMALE',
        date_of_birth='2000-01-01',
        country=None,
        city=None,
        is_registered=True,
    )
    return player
