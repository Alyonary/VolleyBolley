import pytest
from django.core.exceptions import ValidationError
from django.db.utils import IntegrityError
from django.urls import reverse
from rest_framework import status
from pytest_lazy_fixtures import lf

from apps.core.models import GameInvitation


from apps.event.models import Game


@pytest.mark.django_db
class TestGameModel:

    def test_create_game(self, court_obj_with_tag, active_user, game_data):
        players = game_data.pop('players')
        levels = game_data.pop('player_levels')
        game = Game.objects.create(**game_data)
        game.players.set(players)
        game.player_levels.set(levels)

        assert game.court == court_obj_with_tag
        assert game.message == game_data['message']
        assert game.start_time == game_data['start_time']
        assert game.end_time == game_data['end_time']
        assert game.gender == game_data['gender']
        assert list(game.player_levels.all()) == levels
        assert game.is_private == game_data['is_private']
        assert game.max_players == game_data['max_players']
        assert game.price_per_person == game_data['price_per_person']
        assert game.payment_type == game_data['payment_type']
        assert list(game.players.all()) == players
        assert game.host == active_user
        assert game.currency_type == game_data['currency_type']
        assert game.payment_account == game_data['payment_account']

    @pytest.mark.django_db(transaction=True)
    def test_create_game_with_wrong_court(self, game_data):
        game_data.pop('players', )
        game_data.pop('player_levels')
        original_court_id = game_data['court_id']
        try:
            game_data['court_id'] = 0
            with pytest.raises(IntegrityError):
                Game.objects.create(**game_data)
        finally:
            game_data['court_id'] = original_court_id

    @pytest.mark.django_db(transaction=True)
    def test_create_game_without_every_field(self, game_data):
        game_data.pop('players', None)
        game_data.pop('player_levels', None)
        basic_game_data = game_data.copy()
        for field in game_data.copy():
            try:
                field_value = basic_game_data.pop(field)
                with pytest.raises(
                        expected_exception=(IntegrityError, ValidationError)):
                    created_game = Game.objects.create(**basic_game_data)
                    created_game.full_clean()
            finally:
                basic_game_data[field] = field_value


@pytest.mark.django_db
class TestGameAPI:

    @pytest.mark.parametrize(
        'name, args', (
            ('api:games-list', None),
            ('api:games-detail', lf('game_for_args')),
            ('api:games-preview', None),
            ('api:games-my-games', None),
            ('api:games-archive-games', None),
            ('api:games-invited-games', None),
            ('api:games-upcoming-games', None)
            )
    )
    def test_urls_availability(
            self, authored_APIClient, name, args):
        url = reverse(name, args=args)
        response = authored_APIClient.get(url)
        assert response.status_code == status.HTTP_200_OK

    def test_for_invite_creation(
            self, game_without_players, authored_APIClient, bulk_create_users):
        url = reverse(
            'api:games-invite-players',
            args=(game_without_players.id,)
        )
        user_ids = [user.id for user in bulk_create_users]
        data = {'players': user_ids}
        response = authored_APIClient.post(url, data, format='json')
        assert response.status_code == status.HTTP_201_CREATED
        assert GameInvitation.objects.count() == len(user_ids)
        for user in user_ids:
            invite = GameInvitation.objects.filter(
                host=game_without_players.host,
                invited=user,
                game=game_without_players
            ).first()
            assert invite is not None

    def test_for_game_joining(
            self, game_without_players, another_user, another_user_client):
        GameInvitation.objects.create(
            host=game_without_players.host,
            invited=another_user,
            game=game_without_players
        )
        url = reverse(
            'api:games-joining-game', args=(game_without_players.id,))
        assert game_without_players.players.count() == 0
        response = another_user_client.post(url)
        assert another_user in game_without_players.players.all()
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data['is_joined'] is True
        assert GameInvitation.objects.first() is None

    def test_for_game_invitation_declining(
            self,
            game_without_players,
            another_user,
            another_user_client
    ):
        GameInvitation.objects.create(
            host=game_without_players.host,
            invited=another_user,
            game=game_without_players
        )
        url = reverse(
            'api:games-delete-invitation',
            args=(game_without_players.id,)
        )
        assert game_without_players.players.count() == 0
        response = another_user_client.delete(url)
        assert another_user not in game_without_players.players.all()
        assert response.status_code == status.HTTP_204_NO_CONTENT
        assert GameInvitation.objects.first() is None
