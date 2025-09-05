import pytest
from django.core.exceptions import ValidationError
from django.db.utils import IntegrityError
from django.urls import reverse
from pytest_lazy_fixtures import lf
from rest_framework import status

from apps.event.models import Game, GameInvitation


@pytest.mark.django_db
class TestGameModel:

    def test_create_game(self, court_thailand, player_thailand, game_data):
        players = game_data.pop('players')
        levels = game_data.pop('player_levels')
        game = Game.objects.create(**game_data)
        game.players.set(players)
        game.player_levels.set(levels)

        assert game.court == court_thailand
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
        assert game.host == player_thailand
        assert game.currency_type == game_data['currency_type']
        assert game.payment_account == game_data['payment_account']

    @pytest.mark.django_db
    @pytest.mark.parametrize('wrong_data', [
        'Court in Thalland',
        None,
        999
    ])
    def test_create_game_with_wrong_court(self, game_data, wrong_data):
        game_data.pop('players', )
        game_data.pop('player_levels')
        game_data['court_id'] = wrong_data
        with pytest.raises((ValidationError, ValueError, IntegrityError)):
            game = Game.objects.create(**game_data)
            game.full_clean()


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
            self, api_client_thailand, name, args, player_thailand):
        url = reverse(name, args=args)
        response = api_client_thailand.get(url)
        assert response.status_code == status.HTTP_200_OK

    def test_for_invite_creation(
            self,
            game_thailand,
            api_client_thailand,
            bulk_create_registered_players
    ):
        url = reverse(
            'api:games-invite-players',
            args=(game_thailand.id,)
        )
        player_ids = [player.id for player in bulk_create_registered_players]
        data = {'players': player_ids}
        response = api_client_thailand.post(url, data, format='json')
        assert response.status_code == status.HTTP_201_CREATED
        assert GameInvitation.objects.count() == len(player_ids)
        for user in player_ids:
            invite = GameInvitation.objects.filter(
                host=game_thailand.host,
                invited=user,
                game=game_thailand
            ).first()
            assert invite is not None

    def test_for_game_joining(
            self, game_thailand,
            player_cyprus,
            api_client_cyprus
    ):
        GameInvitation.objects.create(
            host=game_thailand.host,
            invited=player_cyprus,
            game=game_thailand
        )
        url = reverse(
            'api:games-joining-game', args=(game_thailand.id,))
        assert game_thailand.players.count() == 0
        response = api_client_cyprus.post(url)
        assert player_cyprus in game_thailand.players.all()
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data['is_joined'] is True
        assert GameInvitation.objects.first() is None

    def test_for_game_invitation_declining(
            self,
            game_thailand,
            api_client_cyprus,
            player_cyprus,

    ):
        GameInvitation.objects.create(
            host=game_thailand.host,
            invited=player_cyprus,
            game=game_thailand
        )
        url = reverse(
            'api:games-delete-invitation',
            args=(game_thailand.id,)
        )
        assert game_thailand.players.count() == 0
        response = api_client_cyprus.delete(url)
        assert player_cyprus not in game_thailand.players.all()
        assert response.status_code == status.HTTP_204_NO_CONTENT
        assert GameInvitation.objects.first() is None

    def test_filtering_queryset(
            self,
            game_thailand,
            game_cyprus,
            player_thailand,
            api_client_thailand,
    ):
        assert Game.objects.count() == 2
        response = api_client_thailand.get(reverse('api:games-list'))
        assert len(response.data) == 1
        assert response.data[0]['game_id'] == game_thailand.id


@pytest.mark.django_db(transaction=False)
class TestGameSerializers:

    def test_game_create_serializer(
            self,
            court_thailand,
            api_client_thailand,
            player_thailand,
            game_levels_light,
            game_levels_medium,
            currency_type_thailand,
            payment_account_revolut
    ):

        game_data = {
            'court_id': court_thailand.id,
            'message': 'Hi! Just old',
            'start_time': '2026-07-01T14:30:00Z',
            'end_time': '2026-07-01T16:30:00Z',
            'gender': 'MEN',
            'levels': [game_levels_light.name,
                       game_levels_medium.name],
            'is_private': False,
            'maximum_players': 5,
            'price_per_person': '5',
            'payment_type': payment_account_revolut.payment_type,
            'players': []
        }
        response = api_client_thailand.post(
            reverse('api:games-list'), data=game_data, format='json')
        assert Game.objects.filter(pk=response.json()['game_id']).exists()
        assert response.status_code == status.HTTP_201_CREATED
        assert response.json() == {
            'game_id': response.json()['game_id'],
            'court_id': court_thailand.id,
            'message': 'Hi! Just old',
            'start_time': '2026-07-01T14:30:00Z',
            'end_time': '2026-07-01T16:30:00Z',
            'gender': 'MEN',
            'levels': [
                'LIGHT',
                'MEDIUM'
            ],
            'is_private': False,
            'maximum_players': 5,
            'price_per_person': '5.00',
            'currency_type': currency_type_thailand.currency_type,
            'payment_type': payment_account_revolut.payment_type,
            'payment_account': payment_account_revolut.payment_account,
            'players': [
                player_thailand.id
            ]
        }

    def test_game_detail_serializer(
            self,
            api_client_thailand,
            player_thailand,
            game_thailand_with_players,
            court_thailand

    ):
        response = api_client_thailand.get(
            reverse('api:games-detail', args=(game_thailand_with_players.id,)))
        response_data = response.json()
        players = response_data.pop('players')
        assert game_thailand_with_players.players.count() == len(players)
        for key in list(players[0].keys()):
            assert key in (
                'player_id', 'first_name', 'last_name', 'level', 'avatar'
            )
        levels = response_data.pop('levels')
        for level in game_thailand_with_players.player_levels.all():
            assert level.name in levels
        assert response_data == {
            'game_id': game_thailand_with_players.id,
            'game_type': 'MY GAMES',
            'host': {
                'player_id': player_thailand.id,
                'first_name': player_thailand.user.first_name,
                'last_name': player_thailand.user.last_name,
                'avatar': player_thailand.avatar,
                'level': player_thailand.level
            },
            'is_private': game_thailand_with_players.is_private,
            'message': game_thailand_with_players.message,
            'court_location': {
                'longitude': court_thailand.location.longitude,
                'latitude': court_thailand.location.latitude,
                'court_name': court_thailand.location.court_name,
                'location_name': court_thailand.location.location_name
            },
            'start_time': game_thailand_with_players.start_time,
            'end_time': game_thailand_with_players.end_time,
            'gender': game_thailand_with_players.gender,
            'price_per_person': game_thailand_with_players.price_per_person,
            'currency_type': (
                game_thailand_with_players.currency_type.currency_type),
            'payment_type': game_thailand_with_players.payment_type,
            'payment_account': game_thailand_with_players.payment_account,
            'maximum_players': game_thailand_with_players.max_players,
        }
