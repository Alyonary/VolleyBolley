from datetime import timedelta

import pytest
# from django.core.exceptions import ValidationError
from django.urls import reverse
# from django.utils.dateparse import parse_datetime
from django.utils.timezone import now
from pytest_lazy_fixtures import lf
from rest_framework import status

from apps.event.models import Tourney, GameInvitation


@pytest.mark.django_db
class TestGameModel:

    @pytest.mark.parametrize('tourney, data', [
        (lf('tourney_thai_ind'), lf('tourney_data_individual')),
        (lf('tourney_thai_team'), lf('tourney_data_team'))
    ])
    def test_create_tourney_ind(
            self,
            tourney,
            player_thailand,
            data
            ):

        assert tourney.court.id == data['court_id']
        assert tourney.message == data['message']
        assert tourney.start_time == data['start_time']
        assert tourney.end_time == data['end_time']
        assert tourney.gender == data['gender']
        assert list(tourney.player_levels.all()) == data['player_levels']
        assert tourney.is_individual == data['is_individual']
        assert tourney.max_players == data['max_players']
        assert tourney.maximum_teams == data['maximum_teams']
        assert tourney.price_per_person == data['price_per_person']
        assert tourney.payment_type == data['payment_type']
        assert tourney.host == player_thailand
        assert tourney.currency_type == data['currency_type']
        assert tourney.payment_account == data['payment_account']


@pytest.mark.django_db
class TestTourneyAPI:

    def test_url_detail(
            self,
            api_client_thailand,
            tourney_for_args
            ):
        """The test of the availability of the url of tournament detail."""
        url = reverse('api:tournaments-detail', args=tourney_for_args)
        response = api_client_thailand.get(url)
        assert response.status_code == status.HTTP_200_OK

    @pytest.mark.parametrize(
            ('is_individual, maximum_players, maximum_teams, '
             'result_max_players, result_max_teams'),
            [(True, 6, None, 6, 1),
             (False, None, 4, 8, 4),
             (True, 6, 3, 6, 1),
             (False, 12, 4, 8, 4),])
    def test_tourney_create(
            self,
            api_client_thailand,
            court_thailand,
            currency_type_thailand,
            game_levels_light,
            player_thailand,
            is_individual,
            maximum_players,
            maximum_teams,
            result_max_players,
            result_max_teams
            ):
        """Testing the creation of a tournament via the API.

        The correctness of creating teams and saving field values
        for each type of tournament is checked.
        """
        url = reverse('api:tournaments-list')
        start_time = now() + timedelta(days=2)
        end_time = start_time + timedelta(hours=6)
        data = {
            "court_id": court_thailand.id,
            "message": "Test tourney",
            "start_time": start_time.strftime("%Y-%m-%dT%H:%M:%SZ"),
            "end_time": end_time.strftime("%Y-%m-%dT%H:%M:%SZ"),
            "is_individual": is_individual,
            "gender": "MEN",
            "levels": [
                "LIGHT"
            ],
            "maximum_players": maximum_players,
            "maximum_teams": maximum_teams,
            "price_per_person": "5",
            "payment_type": "REVOLUT",
            "players": [
                    ]
        }
        response = api_client_thailand.post(url, data, format='json')
        created_tourney = Tourney.objects.last()
        assert response.status_code == status.HTTP_201_CREATED
        assert response.data['maximum_players'] == result_max_players
        assert response.data['maximum_teams'] == result_max_teams
        assert response.data['tournament_id'] == created_tourney.id
        assert len(response.data['teams']) == result_max_teams
        assert created_tourney.host == player_thailand
        assert player_thailand in created_tourney.players

    @pytest.mark.parametrize(
            ('tourney'),
            [lf('tourney_thai_ind'),
             lf('tourney_thai_team')])
    def test_for_invite_creation(
            self,
            tourney,
            api_client_thailand,
            bulk_create_registered_players
    ):
        url = reverse(
            'api:tournaments-invite-players',
            args=(tourney.id,)
        )
        player_ids = [
            player.id for player in bulk_create_registered_players
        ]
        data = {'players': player_ids}
        response = api_client_thailand.post(url, data, format='json')
        assert response.status_code == status.HTTP_201_CREATED
        assert GameInvitation.objects.count() == len(player_ids)
        for user in player_ids:
            invite = tourney.event_invites.filter(
                invited=user
            ).first()
            assert invite is not None

#     def test_for_game_joining(
#             self, game_thailand,
#             player_cyprus,
#             api_client_cyprus
#     ):
#         GameInvitation.objects.create(
#             host=game_thailand.host,
#             invited=player_cyprus,
#             content_object=game_thailand
#         )
#         url = reverse(
#             'api:games-joining-game', args=(game_thailand.id,))
#         assert game_thailand.players.count() == 0
#         response = api_client_cyprus.post(url)
#         assert player_cyprus in game_thailand.players.all()
#         assert response.status_code == status.HTTP_200_OK
#         data = response.json()
#         assert data['is_joined'] is True
#         assert GameInvitation.objects.first() is None

#     def test_for_game_invitation_declining(
#             self,
#             game_thailand,
#             api_client_cyprus,
#             player_cyprus,

#     ):
#         GameInvitation.objects.create(
#             host=game_thailand.host,
#             invited=player_cyprus,
#             content_object=game_thailand
#         )
#         url = reverse(
#             'api:games-delete-invitation',
#             args=(game_thailand.id,)
#         )
#         assert game_thailand.players.count() == 0
#         response = api_client_cyprus.delete(url)
#         assert player_cyprus not in game_thailand.players.all()
#         assert response.status_code == status.HTTP_204_NO_CONTENT
#         assert GameInvitation.objects.first() is None

#     def test_filtering_queryset(
#             self,
#             game_thailand,
#             game_cyprus,
#             player_thailand,
#             api_client_thailand,
#     ):
#         assert Game.objects.count() == 2
#         response = api_client_thailand.get(
#             reverse('api:games-upcoming-games')
#         )
#         assert len(response.data['games']) == 1
#         assert response.data['games'][0]['game_id'] == game_thailand.id

#     def test_deleting_game_by_host(
#             self,
#             api_client_thailand,
#             game_thailand,
#             game_for_args
#     ):
#         assert Game.objects.count() == 1
#         response = api_client_thailand.delete(
#             reverse('api:games-detail', args=game_for_args))
#         assert response.status_code == status.HTTP_204_NO_CONTENT
#         assert Game.objects.count() == 0

#     def test_deleting_game_by_non_host(
#             self,
#             player_thailand_female_pro,
#             game_thailand,
#             game_for_args,
#             client
#     ):
#         client.force_authenticate(player_thailand_female_pro.user)
#         assert Game.objects.count() == 1
#         response = client.delete(
#             reverse('api:games-detail', args=game_for_args))
#         assert response.status_code == status.HTTP_403_FORBIDDEN
#         assert Game.objects.count() == 1


# @pytest.mark.django_db(transaction=False)
# class TestGameSerializers:

#     def test_game_create_serializer(
#             self,
#             court_thailand,
#             api_client_thailand,
#             player_thailand,
#             currency_type_thailand,
#             payment_account_revolut,
#             game_create_data
#     ):

#         response = api_client_thailand.post(
#             reverse('api:games-list'),
#             data=game_create_data,
#             format='json'
#         )

#         assert response.status_code == status.HTTP_201_CREATED
#         assert Game.objects.filter(
#             pk=response.json()['game_id']
#         ).exists()

#         response_data = response.json()

#         assert response_data['court_id'] == court_thailand.id
#         assert response_data['message'] == game_create_data['message']
#         assert response_data['gender'] == game_create_data['gender']
#         assert response_data['levels'] == game_create_data['levels']
#         assert response_data['is_private'] == game_create_data['is_private']
#         assert (response_data['maximum_players'] ==
#                 game_create_data['maximum_players'])
#         assert (response_data['price_per_person'] ==
#                 game_create_data['price_per_person'])
#         assert (response_data['currency_type'] ==
#                 currency_type_thailand.currency_type)
#         assert (response_data['payment_type'] ==
#                 game_create_data['payment_type'])
#         assert (response_data['payment_account'] ==
#                 payment_account_revolut.payment_account)
#         assert response_data['players'] == [player_thailand.id]
#         assert response_data['start_time'] == game_create_data['start_time']
#         assert response_data['end_time'] == game_create_data['end_time']
#         assert 'game_id' in response_data
#         assert isinstance(response_data['game_id'], int)

#     def test_game_detail_serializer(
#             self,
#             api_client_thailand,
#             player_thailand,
#             game_thailand_with_players,
#             court_thailand
#     ):
#         response = api_client_thailand.get(
#             reverse(
#                 'api:games-detail',
#                 args=(game_thailand_with_players.id,)
#             )
#         )
#         response_data = response.json()

#         players = response_data.pop('players')
#         assert game_thailand_with_players.players.count() == len(players)
#         for key in list(players[0].keys()):
#             assert key in (
#                 'player_id', 'first_name', 'last_name', 'level', 'avatar'
#             )

#         levels = response_data.pop('levels')
#         for level in game_thailand_with_players.player_levels.all():
#             assert level.name in levels

#         assert (response_data['game_id'] ==
#                 game_thailand_with_players.id)
#         assert (response_data['is_private'] ==
#                 game_thailand_with_players.is_private)
#         assert (response_data['message'] ==
#                 game_thailand_with_players.message)
#         assert (response_data['gender'] ==
#                 game_thailand_with_players.gender)
#         assert (response_data['price_per_person'] ==
#                 game_thailand_with_players.price_per_person)
#         assert (response_data['currency_type'] ==
#                 game_thailand_with_players.currency_type.currency_type)
#         assert (response_data['payment_type'] ==
#                 game_thailand_with_players.payment_type)
#         assert (response_data['payment_account'] ==
#                 game_thailand_with_players.payment_account)
#         assert (response_data['maximum_players'] ==
#                 game_thailand_with_players.max_players)

#         host = response_data['host']
#         assert host['player_id'] == player_thailand.id
#         assert host['first_name'] == player_thailand.user.first_name
#         assert host['last_name'] == player_thailand.user.last_name
#         assert host['avatar'] == player_thailand.avatar
#         assert host['level'] == player_thailand.rating.grade

#         court = response_data['court_location']
#         assert court['longitude'] == court_thailand.location.longitude
#         assert court['latitude'] == court_thailand.location.latitude
#         assert court['court_name'] == court_thailand.location.court_name
#         assert (court['location_name'] ==
#                 court_thailand.location.location_name)

#         assert (parse_datetime(response_data['start_time']) ==
#                 game_thailand_with_players.start_time)
#         assert (parse_datetime(response_data['end_time']) ==
#                 game_thailand_with_players.end_time)

#     @pytest.mark.parametrize(('field, value'), [
#         ('start_time', '2024-07-01T14:30:00Z'),
#         ('end_time', '2024-07-01T14:30:00Z'),
#         ('gender', 'Wrong gender'),
#         ('levels', ['Wrong levels'])
#     ])
#     def test_create_game_with_wrong_data(
#             self,
#             game_create_data,
#             api_client_thailand,
#             field,
#             value
#     ):
#         wrong_data = game_create_data
#         wrong_data[field] = value
#         response = api_client_thailand.post(
#             reverse('api:games-list'),
#             data=game_create_data,
#             format='json'
#         )
#         assert response.status_code == status.HTTP_400_BAD_REQUEST

#     def test_level_validation_in_game_invitation(
#             self,
#             player_thailand_female_pro,
#             api_client_thailand,
#             game_for_args
#     ):
#         response = api_client_thailand.post(
#             reverse('api:games-invite-players', args=game_for_args),
#             data={'players': [player_thailand_female_pro.id,]}
#         )
#         assert response.status_code == status.HTTP_400_BAD_REQUEST
#         assert response.data.get('invited')

#     def test_game_short_serializer(
#             self,
#             game_thailand,
#             game_thailand_with_players
#     ):
#         games = Game.objects.all()
#         serializer = GameShortSerializer(games, many=True)
#         result = serializer.data[0]
#         assert result['game_id'] == game_thailand.id
#         assert result['message'] == game_thailand.message

#         assert (parse_datetime(result['start_time']) ==
#                 game_thailand.start_time)
#         assert (parse_datetime(result['end_time']) ==
#                 game_thailand.end_time)

#         host = result['host']
#         assert host['player_id'] == game_thailand.host.id
#         assert host['first_name'] == game_thailand.host.user.first_name
#         assert host['last_name'] == game_thailand.host.user.last_name
#         assert host['avatar'] == game_thailand.host.avatar
#         assert host['level'] == game_thailand.host.rating.grade

#         court = result['court_location']
#         assert court['longitude'] == game_thailand.court.location.longitude
#         assert court['latitude'] == game_thailand.court.location.latitude
#         assert (court['court_name'] ==
#                 game_thailand.court.location.court_name)
#         assert (court['location_name'] ==
#                 game_thailand.court.location.location_name)


# @pytest.mark.django_db()
# class TestGameFiltering:

#     def test_preview_filtering(
#             self,
#             api_client_thailand,
#             game_data,
#             game_thailand,
#             player_thailand
#     ):
#         nearest_time = now() + timedelta(minutes=5)
#         nearest_time = nearest_time.strftime("%Y-%m-%dT%H:%M:%SZ")
#         game_data['start_time'] = nearest_time
#         game_data.pop('players')
#         game_data.pop('player_levels')
#         Game.objects.create(**game_data)
#         assert Game.objects.count() == 2
#         response = api_client_thailand.get(reverse('api:games-preview'))
#         assert response.json() == {
#             'upcoming_game_time': nearest_time,
#             'invites': 0
#         }

#     def test_preview_with_invites(
#             self,
#             api_client_thailand,
#             player_thailand,
#             game_cyprus
#     ):
#         GameInvitation.objects.create(
#             content_object=game_cyprus,
#             host=game_cyprus.host,
#             invited=player_thailand
#         )
#         response = api_client_thailand.get(reverse('api:games-preview'))
#         assert response.json() == {
#             'upcoming_game_time': None,
#             'invites': 1
#         }

#     def test_my_games_filtering(
#             self,
#             api_client_thailand,
#             game_thailand,
#             game_thailand_with_players,
#             player_thailand_female_pro
#     ):
#         game_thailand_with_players.host = player_thailand_female_pro
#         game_thailand_with_players.save()
#         assert Game.objects.count() == 2
#         response = api_client_thailand.get(reverse('api:games-my-games'))
#         assert len(response.data['games']) == 1
#         assert (response.data['games'][0]['game_id'] ==
#                 game_thailand.id)

#     def test_archive_filtering(
#             self,
#             player_thailand,
#             game_thailand,
#             game_thailand_with_players,
#     ):
#         game_thailand_with_players.start_time = (
#             now() - timedelta(weeks=520)
#         )
#         game_thailand_with_players.save()
#         assert Game.objects.count() == 2
#         result = Game.objects.archive_games(player_thailand)
#         assert len(result) == 1
#         assert result[0].id == game_thailand_with_players.id

#     def test_invites_filtering(
#             self,
#             game_thailand,
#             game_thailand_with_players,
#             player_thailand_female_pro
#     ):
#         games = Game.objects.invited_games(player_thailand_female_pro)
#         assert not games

#         GameInvitation.objects.create(
#             content_object=game_thailand,
#             host=game_thailand.host,
#             invited=player_thailand_female_pro
#         )
#         games = Game.objects.invited_games(player_thailand_female_pro)
#         assert len(games) == 1
#         assert games.first() == game_thailand

#     def test_upcoming_filtering(
#             self,
#             game_thailand,
#             game_thailand_with_players,
#             player_thailand_female_pro
#     ):
#         upcomming_games = Game.objects.upcomming_games(
#             player_thailand_female_pro
#         )
#         assert not upcomming_games
#         game_thailand.players.add(player_thailand_female_pro)
#         upcomming_games = Game.objects.upcomming_games(
#             player_thailand_female_pro
#         )
#         assert len(upcomming_games) == 1
#         assert upcomming_games.first() == game_thailand
