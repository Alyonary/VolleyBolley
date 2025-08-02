import pytest
from apps.players.models import Player, PlayerLocation


@pytest.fixture
def sample_location():
    return PlayerLocation.objects.create(
        country='Russia',
        city='Moscow'
    )


@pytest.fixture
def player_data(active_user, sample_location):
    return {
        'user': active_user,
        'gender': 'MALE',
        'level': 'LIGHT',
        'location': sample_location
    }


@pytest.fixture
def player_male_light(player_data):
    return Player.objects.create(**player_data)
