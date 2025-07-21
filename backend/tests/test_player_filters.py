import pytest
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient

from apps.api.filters import PlayersFilter
from apps.players.models import Player, PlayerLocation

User = get_user_model()


@pytest.mark.django_db
class TestPlayersFilter:
    """Tests for player filter."""

    @pytest.fixture
    def setup_test_data(self):
        """Creates test data for filters."""
        limassol = PlayerLocation.objects.create(
            country="Cyprus", city="Limassol"
        )
        bangkok = PlayerLocation.objects.create(
            country="Thailand", city="Bangkok"
        )

        user1 = User.objects.create_user(
            username="john_doe",
            first_name="John",
            last_name="Doe",
            email="john@example.com",
        )
        user2 = User.objects.create_user(
            username="jane_smith",
            first_name="Jane",
            last_name="Smith",
            email="jane@example.com",
        )
        user3 = User.objects.create_user(
            username="bob_wilson",
            first_name="Bob",
            last_name="Wilson",
            email="bob@example.com",
        )
        player1 = Player.objects.create(
            user=user1, gender="MALE", level="LIGHT", location=limassol
        )
        player2 = Player.objects.create(
            user=user2, gender="FEMALE", level="PRO", location=bangkok
        )
        player3 = Player.objects.create(
            user=user3, gender="MALE", level="LIGHT", location=limassol
        )

        return {
            "players": [player1, player2, player3],
            "locations": [limassol, bangkok],
            "users": [user1, user2, user3],
        }

    def test_filter_by_username(self, setup_test_data):
        """Test filtering by username."""
        data = {"username": "john"}
        filter_instance = PlayersFilter(data, queryset=Player.objects.all())
        filtered_players = filter_instance.qs
        assert filtered_players.count() == 1
        assert filtered_players.first().user.username == "john_doe"

    def test_filter_by_first_name(self, setup_test_data):
        """Test filtering by first name."""
        data = {"first_name": "Jane"}
        filter_instance = PlayersFilter(data, queryset=Player.objects.all())

        filtered_players = filter_instance.qs
        assert filtered_players.count() == 1
        assert filtered_players.first().user.first_name == "Jane"

    def test_filter_by_last_name(self, setup_test_data):
        """Test filtering by last name."""
        data = {"last_name": "smith"}
        filter_instance = PlayersFilter(data, queryset=Player.objects.all())

        filtered_players = filter_instance.qs
        assert filtered_players.count() == 1
        assert filtered_players.first().user.last_name == "Smith"

    def test_filter_by_location(self, setup_test_data):
        """Test filtering by city."""
        data = {"location": "Limassol"}
        filter_instance = PlayersFilter(data, queryset=Player.objects.all())

        filtered_players = filter_instance.qs
        assert filtered_players.count() == 2

        for player in filtered_players:
            assert player.location.city == "Limassol"

    def test_filter_by_level(self, setup_test_data):
        """Test filtering by level."""
        data = {"level_type": "LIGHT"}
        filter_instance = PlayersFilter(data, queryset=Player.objects.all())

        filtered_players = filter_instance.qs
        assert filtered_players.count() == 2

        for player in filtered_players:
            assert player.level == "LIGHT"

    def test_multiple_filters(self, setup_test_data):
        """Test combined filters."""
        data = {"location": "Limassol", "level_type": "LIGHT"}
        filter_instance = PlayersFilter(data, queryset=Player.objects.all())

        filtered_players = filter_instance.qs
        assert filtered_players.count() == 2

        for player in filtered_players:
            assert player.location.city == "Limassol"
            assert player.level == "LIGHT"

    def test_no_results_filter(self, setup_test_data):
        """Test filter with no results."""
        data = {"username": "nonexistent"}
        filter_instance = PlayersFilter(data, queryset=Player.objects.all())

        filtered_players = filter_instance.qs
        assert filtered_players.count() == 0

    def test_empty_filter(self, setup_test_data):
        """Test empty filter should return all players."""
        data = {}
        filter_instance = PlayersFilter(data, queryset=Player.objects.all())

        filtered_players = filter_instance.qs
        assert filtered_players.count() == 3

    def test_case_insensitive_search(self, setup_test_data):
        """Test case insensitive search."""
        data = {"first_name": "JOHN"}
        filter_instance = PlayersFilter(data, queryset=Player.objects.all())

        filtered_players = filter_instance.qs
        assert filtered_players.count() == 1
        assert filtered_players.first().user.first_name == "John"


@pytest.mark.django_db
class TestPlayersFilterAPI:
    """Class for API filter tests."""

    pass
