import pytest
from django.db.utils import IntegrityError
from django.urls import reverse
from pytest_lazy_fixtures import lf
from rest_framework import status

from apps.event.models import Game, GameInvitation


@pytest.mark.django_db
class TestGameModel:

    def test_create_game(self, court_obj_with_tag, user_player, game_data):
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
        assert game.host == user_player
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
            self, authored_api_client, name, args, user_player):
        url = reverse(name, args=args)
        response = authored_api_client.get(url)
        assert response.status_code == status.HTTP_200_OK

    def test_for_invite_creation(
            self,
            game_without_players,
            authored_api_client,
            bulk_create_registered_players
    ):
        url = reverse(
            'api:games-invite-players',
            args=(game_without_players.id,)
        )
        player_ids = [player.id for player in bulk_create_registered_players]
        data = {'players': player_ids}
        response = authored_api_client.post(url, data, format='json')
        assert response.status_code == status.HTTP_201_CREATED
        assert GameInvitation.objects.count() == len(player_ids)
        for user in player_ids:
            invite = GameInvitation.objects.filter(
                host=game_without_players.host,
                invited=user,
                game=game_without_players
            ).first()
            assert invite is not None

    def test_for_game_joining(
            self, game_without_players,
            another_user_player,
            another_user_client
    ):
        GameInvitation.objects.create(
            host=game_without_players.host,
            invited=another_user_player,
            game=game_without_players
        )
        url = reverse(
            'api:games-joining-game', args=(game_without_players.id,))
        assert game_without_players.players.count() == 0
        response = another_user_client.post(url)
        assert another_user_player in game_without_players.players.all()
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data['is_joined'] is True
        assert GameInvitation.objects.first() is None

    def test_for_game_invitation_declining(
            self,
            game_without_players,
            another_user_player,
            another_user_client
    ):
        GameInvitation.objects.create(
            host=game_without_players.host,
            invited=another_user_player,
            game=game_without_players
        )
        url = reverse(
            'api:games-delete-invitation',
            args=(game_without_players.id,)
        )
        assert game_without_players.players.count() == 0
        response = another_user_client.delete(url)
        assert another_user_player not in game_without_players.players.all()
        assert response.status_code == status.HTTP_204_NO_CONTENT
        assert GameInvitation.objects.first() is None

    def test_filtering_queryset(
            self,
            game_without_players,
            another_game_cyprus,
            user_player,
            authored_api_client,
    ):
        assert Game.objects.count() == 2
        response = authored_api_client.get(reverse('api:games-list'))
        assert len(response.data) == 1
        assert response.data[0]['game_id'] == game_without_players.id


@pytest.mark.django_db(transaction=False)
class TestGameSerializers:

    def test_game_create_serializer(
            self,
            court_obj,
            authored_api_client,
            user_player,
            game_levels,
            currency_type
    ):

        payload = {
            'court_id': court_obj.id,
            'message': 'Hi! Just old',
            'start_time': '2025-07-01T14:30:00Z',
            'end_time': '2025-07-01T14:30:00Z',
            'gender': 'MEN',
            'levels': [game_levels.name],
            'is_private': False,
            'maximum_players': 5,
            'price_per_person': '5',
            'payment_type': 'REVOLUT',
            'players': []
        }
        response = authored_api_client.post(
            reverse('api:games-list'), data=payload, format='json')
        assert Game.objects.filter(pk=response.json()['game_id']).exists()
        assert response.status_code == status.HTTP_201_CREATED
        assert response.json() == {
            'game_id': response.json()['game_id'],
            'court_id': court_obj.id,
            'message': 'Hi! Just old',
            'start_time': '2025-07-01T14:30:00Z',
            'end_time': '2025-07-01T14:30:00Z',
            'gender': 'MEN',
            'levels': [
                'LIGHT'
            ],
            'is_private': False,
            'maximum_players': 5,
            'price_per_person': '5.00',
            'currency_type': 'THB',
            'payment_type': 'REVOLUT',
            'payment_account': 'Not defined',
            'players': [
                user_player.id
            ]
        }

    def test_game_detail_serializer(
            self,
            authored_api_client,
            user_player,
            game_with_players,
            game_for_args,
            game_data,
            court_obj

    ):
        response = authored_api_client.get(
            reverse('api:games-detail', args=game_for_args))
        response_data = response.json()
        players = response_data.pop('players')
        assert game_with_players.players.count() == len(players)
        for key in list(players[0].keys()):
            assert key in (
                'player_id', 'first_name', 'last_name', 'level', 'avatar'
            )
        assert response_data == {
            'game_id': game_with_players.id,
            'game_type': 'MY GAMES',
            'host': {
                'player_id': user_player.id,
                'first_name': user_player.user.first_name,
                'last_name': user_player.user.last_name,
                'avatar': None,
                'level': 'LIGHT'
            },
            'is_private': False,
            'message': game_data['message'],
            'court_location': {
                'longitude': court_obj.location.longitude,
                'latitude': court_obj.location.latitude,
                'court_name': court_obj.location.court_name,
                'location_name': court_obj.location.location_name
            },
            'start_time': '2025-08-21T15:30:00Z',
            'end_time': '2025-08-21T18:30:00Z',
            'levels': [
                'LIGHT'
            ],
            'gender': 'MEN',
            'price_per_person': '5.00',
            'currency_type': 'THB',
            'payment_type': 'REVOLUT',
            'payment_account': 'test acc',
            'maximum_players': game_data['max_players'],
        }
