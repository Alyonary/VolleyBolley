import pytest
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.db import IntegrityError

from apps.players.models import Player

User = get_user_model()


@pytest.mark.django_db
class TestPlayerModel:

    def test_create_player_with_required_fields(
        self, active_user, sample_location, player_data
    ):
        player = Player.objects.create(**player_data)

        assert player.user == active_user
        assert player.gender == 'MALE'
        assert player.level == 'LIGHT'
        assert player.location == sample_location
        assert player.rating == 1

    def test_player_user_relationship(self, active_user, player_male_light):

        assert active_user.player == player_male_light

    def test_player_location_relationship(
        self, sample_location, player_male_light
    ):

        assert player_male_light.location == sample_location
        assert sample_location.player_set.first() == player_male_light

    def test_player_without_user_fails(self, player_data):
        with pytest.raises(IntegrityError):
            player_data.pop('user')
            Player.objects.create(**player_data)

    def test_player_without_gender_default(self, player_data):
        player_data.pop('gender')
        player = Player.objects.create(**player_data)

        assert player.gender == 'MALE'

    def test_player_gender_choices_validation(
        self, player_data
    ):
        with pytest.raises(ValidationError):
            player_data_invalid_gender = player_data.update(
                {'gender': 'invalid'}
            )
            player = Player(player_data_invalid_gender)
            player.full_clean()

    def test_player_level_choices_validation(
        self, player_data
    ):
        with pytest.raises(ValidationError):
            player_data_invalid_level = player_data.update(
                {'level': 'invalid'}
            )
            player = Player(player_data_invalid_level)
            player.full_clean()

    def test_player_default_level(self, player_data):
        player_data.pop('level')
        player = Player.objects.create(**player_data)

        assert player.level == 'LIGHT'

    def test_player_optional_location(self, player_data):
        player_data.update(
            {'location': None}
        )
        player = Player.objects.create(**player_data)

        assert player.location is None
