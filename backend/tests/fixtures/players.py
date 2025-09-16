import pytest

from apps.players.models import Player


@pytest.fixture
def player_data(active_user):
    return {
        'user': active_user,
        'gender': 'MALE',
        'level': 'LIGHT',
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
def bulk_create_registered_players(bulk_create_users):
    players = []
    for user in bulk_create_users:
        player, _ = Player.objects.get_or_create(user=user)
        player.is_registered = True
        player.rating.grade = 'PRO'
        player.save()
        players.append(player)
    return players


@pytest.fixture
def player_male_light(player_data):
    grade = player_data.pop('level')
    player = Player.objects.create(**player_data)
    player.rating.grade = grade
    player.rating.save()
    return player

@pytest.fixture
def player_data_for_registration(countries_cities):
    return {
        'first_name': 'TestPlayerName',
        'last_name': 'TestPlayerSurname',
        'gender': 'FEMALE',
        'level': 'LIGHT',
        'date_of_birth': '2000-01-01',
        'country': countries_cities['Thailand'].id,
        'city': countries_cities['Thailand'].cities.filter(
            name='Bangkok'
        ).first().id,
    }


@pytest.fixture
def player_not_default_data(countries_cities, active_user):
    return {
        'user': active_user,
        'gender': 'FEMALE',
        'date_of_birth': '2000-01-01',
        'country': countries_cities['Thailand'],
        'city': countries_cities['Thailand'].cities.filter(
            name='Bangkok'
        ).first(),
    }

@pytest.fixture
def player_grade():
    return 'PRO'