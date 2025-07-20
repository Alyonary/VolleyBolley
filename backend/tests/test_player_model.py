import pytest
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.db import IntegrityError

from apps.players.models import Player, PlayerLocation

User = get_user_model()


@pytest.mark.django_db
class TestPlayerModel:
    @pytest.fixture
    def sample_location(self):
        return PlayerLocation.objects.create(
            country='Russia',
            city='Moscow'
        )

    def test_create_player_with_required_fields(
        self, active_user, sample_location
    ):
        player = Player.objects.create(
            user=active_user,
            gender='male',
            level='light',
            location=sample_location
        )

        assert player.user == active_user
        assert player.gender == 'male'
        assert player.level == 'light'
        assert player.location == sample_location
        assert player.rating == 1

    def test_player_user_relationship(self, active_user, sample_location):
        player = Player.objects.create(
            user=active_user,
            gender='male',
            level='light',
            location=sample_location
        )

        assert active_user.player.first() == player

    def test_player_location_relationship(self, active_user, sample_location):
        player = Player.objects.create(
            user=active_user,
            gender='male',
            level='light',
            location=sample_location
        )

        assert player.location == sample_location
        assert sample_location.player_set.first() == player

    def test_player_without_user_fails(self, sample_location):
        with pytest.raises(IntegrityError):
            Player.objects.create(
                gender='male',
                level='light',
                location=sample_location
            )

    def test_player_without_gender_fails(self, active_user, sample_location):
        player = Player.objects.create(
            user=active_user,
            level='light',
            location=sample_location
        )

        assert player.gender == 'male'

    def test_player_gender_choices_validation(
        self, active_user, sample_location
    ):
        with pytest.raises(ValidationError):
            player = Player(
                user=active_user,
                gender='invalid',
                level='light',
                location=sample_location
            )
            player.full_clean()

    def test_player_level_choices_validation(
        self, active_user, sample_location
    ):
        with pytest.raises(ValidationError):
            player = Player(
                user=active_user,
                gender='male',
                level='invalid',
                location=sample_location
            )
            player.full_clean()

    def test_player_default_level(self, active_user, sample_location):
        player = Player.objects.create(
            user=active_user,
            gender='male',
            location=sample_location
        )

        assert player.level == 'light'

    def test_player_default_rating(self, active_user, sample_location):
        player = Player.objects.create(
            user=active_user,
            gender='male',
            level='light',
            location=sample_location
        )

        assert player.rating == 1

    def test_player_optional_location(self, active_user):
        player = Player.objects.create(
            user=active_user,
            gender='male',
            level='light',
            location=None
        )

        assert player.location is None
