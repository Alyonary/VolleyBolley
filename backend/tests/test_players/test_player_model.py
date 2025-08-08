from datetime import date, timedelta

import pytest
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.db import IntegrityError

from apps.players.models import Player

User = get_user_model()


@pytest.mark.django_db
class TestPlayerModel:

    def test_create_default_player(
        self, active_user
    ):
        player = Player.objects.create(user=active_user)

        assert player.user == active_user
        assert player.gender == 'MALE'
        assert player.level == 'LIGHT'
        assert player.rating == 1
        assert player.country is None
        assert player.city is None
        assert not player.avatar
        assert player.date_of_birth == '2000-01-01'
        assert player.is_registered is False

    def test_not_default_player(self, player_not_default_data, active_user):
        player = Player.objects.create(**player_not_default_data)
        assert player.user == active_user
        assert player.gender == 'FEMALE'
        assert player.level == 'PRO'
        assert player.rating == 10
        assert player.country.__str__() == 'Thailand'
        assert player.city.__str__() == 'Bangkok, Thailand'
        assert not player.avatar
        assert player.date_of_birth == '2000-01-01'
        assert not player.is_registered

    def test_player_user_relationship(self, active_user, player_male_light):
        assert active_user.player == player_male_light

    def test_player_without_user_fails(self, player_not_default_data):
        with pytest.raises(IntegrityError):
            player_not_default_data.pop('user')
            Player.objects.create(**player_not_default_data)

    def test_player_gender_choices_validation(
        self, player_not_default_data
    ):
        with pytest.raises(ValidationError):
            player_not_default_data.update(
                {'gender': 'invalid'}
            )
            player = Player(**player_not_default_data)
            player.full_clean()

    def test_player_level_choices_validation(
        self, player_not_default_data
    ):
        with pytest.raises(ValidationError):
            player_not_default_data.update(
                {'level': 'invalid'}
            )
            player = Player(**player_not_default_data)
            player.full_clean()

    def test_player_with_bad_birthday_format(self, player_not_default_data):
        with pytest.raises(ValidationError):
            player_not_default_data.update(
                {'date_of_birth': '12:01:1998'}
            )
            player = Player(**player_not_default_data)
            player.full_clean()

    def test_players_birthday_in_future(self, player_not_default_data):
        with pytest.raises(ValidationError):
            future_date = date.today() + timedelta(days=(1))
            player_not_default_data.update(
                {'date_of_birth': future_date}
            )
            player = Player(**player_not_default_data)
            player.full_clean()
