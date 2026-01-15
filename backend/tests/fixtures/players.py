import pytest

from apps.players.models import Player


@pytest.fixture
def player_data(active_user):
    return {
        'user': active_user,
        'gender': 'MALE',
        'level': 'LIGHT',
        'is_registered': True,
    }


@pytest.fixture
def player_updated_data(countries_cities):
    return {
        'first_name': 'UpdatedName',
        'last_name': 'UpdatedLastName',
        'country': countries_cities['Cyprus'].id,
        'city': countries_cities['Cyprus']
        .cities.filter(name='Paphos')
        .first()
        .id,
        'date_of_birth': '1995-05-05',
        'gender': 'MALE',
        'avatar': 'fake-base64-str',
        'level': 'PRO',
        'is_registered': False,
    }


@pytest.fixture
def player_partial_updated_data():
    return {
        'last_name': 'PartialUpdateLastName',
        'date_of_birth': '1995-05-05',
    }


@pytest.fixture
def player_generated_after_login_data(user_generated_after_login):
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
def registered_player_data(user_with_registered_player):
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
def bulk_create_not_registered_players(bulk_create_users):
    players = []
    for user in bulk_create_users:
        player, _ = Player.objects.get_or_create(user=user)
        player.is_registered = False
        player.save()
        players.append(player)
    return players


@pytest.fixture
def bulk_create_registered_players(bulk_create_users, countries_cities):
    players = []
    for user in bulk_create_users[:2]:
        player, _ = Player.objects.get_or_create(user=user)
        player.is_registered = True
        player.country = countries_cities['Cyprus']
        player.city = (
            countries_cities['Cyprus'].cities.filter(name='Paphos').first()
        )
        player.save()
        players.append(player)
    for user in bulk_create_users[2:]:
        player, _ = Player.objects.get_or_create(user=user)
        player.is_registered = True
        player.country = countries_cities['Thailand']
        player.city = (
            countries_cities['Thailand'].cities.filter(name='Bangkok').first()
        )
        player.save()
        players.append(player)
    return players


@pytest.fixture
def player_male_light(player_data):
    grade = player_data.pop('level')
    player = Player.objects.create(**player_data)
    rating = player.rating
    rating.grade = grade
    rating.save()
    return player


@pytest.fixture
def player_data_for_registration(countries_cities):
    return {
        'first_name': 'RegisterPlayerName',
        'last_name': 'RegisterPlayerSurname',
        'gender': 'FEMALE',
        'level': 'MEDIUM',
        'date_of_birth': '1990-06-06',
        'country': countries_cities['Thailand'].id,
        'city': countries_cities['Thailand']
        .cities.filter(name='Bangkok')
        .first()
        .id,
        'avatar': 'registered-player-fake-avatar',
        'is_registered': False,
    }


@pytest.fixture
def player_no_data_for_registration():
    return {}


@pytest.fixture
def player_necessary_data_for_registration(countries_cities):
    return {
        'first_name': 'Name',
        'last_name': 'LastName',
        'country': countries_cities['Thailand'].id,
        'city': countries_cities['Thailand']
        .cities.filter(name='Bangkok')
        .first()
        .id,
        'level': 'MEDIUM',
        'date_of_birth': '1990-06-06',
        'gender': 'FEMALE',
    }


@pytest.fixture
def player_not_default_data(countries_cities, active_user):
    return {
        'user': active_user,
        'gender': 'FEMALE',
        'date_of_birth': '2000-01-01',
        'country': countries_cities['Thailand'],
        'city': countries_cities['Thailand']
        .cities.filter(name='Bangkok')
        .first(),
    }


@pytest.fixture
def player_grade():
    return 'PRO'
