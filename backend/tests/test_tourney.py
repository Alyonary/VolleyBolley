from datetime import timedelta

import pytest

# from django.core.exceptions import ValidationError
from django.urls import reverse
from django.utils.dateparse import parse_datetime
from django.utils.timezone import now
from pytest_lazy_fixtures import lf
from rest_framework import status

from apps.event.models import GameInvitation, Tourney, TourneyTeam
from apps.event.serializers import TourneyShortSerializer


@pytest.mark.django_db
class TestTourneyModel:

    @pytest.mark.parametrize('tourney, data', [
        (lf('tourney_thai_ind'), lf('tourney_data_individual')),
        (lf('tourney_thai_team'), lf('tourney_data_team'))
    ])
    def test_create_tourney(
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
        if tourney.is_individual:
            assert tourney.maximum_teams == 1
        else:
            assert tourney.maximum_teams == data['maximum_teams']
        assert tourney.price_per_person == data['price_per_person']
        assert tourney.payment_type == data['payment_type']
        assert tourney.host == player_thailand
        assert tourney.currency_type == data['currency_type']
        assert tourney.payment_account == data['payment_account']
        assert TourneyTeam.objects.filter(tourney=tourney).exists()
        assert tourney.teams.count() == tourney.maximum_teams

    @pytest.mark.parametrize('tourney', [
        (lf('tourney_thai_ind')),
        (lf('tourney_thai_team'))
    ])
    def test_create_tourney_teams(
            self,
            tourney
            ):
        assert tourney.teams.count() == tourney.maximum_teams


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
        assert created_tourney.teams.count() == result_max_teams

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

    def test_create_invitation_wrong_level(
            self,
            tourney_thai_ind,
            api_client_thailand,
            player_thailand_female_pro
            ):
        levels = [level.name for level in tourney_thai_ind.player_levels.all()]
        assert player_thailand_female_pro.rating.grade not in levels
        url = reverse(
            'api:tournaments-invite-players',
            args=(tourney_thai_ind.id,)
        )
        data = {'players': [player_thailand_female_pro.id,]}
        response = api_client_thailand.post(url, data, format='json')
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert GameInvitation.objects.count() == 0


@pytest.mark.django_db
class TestTourney:

    def test_first(self, create_custom_tourney):
        new_tourney = create_custom_tourney(message='new tourney')
        assert isinstance(new_tourney, Tourney)
        assert Tourney.objects.count() == 1
        anotehr_tourney = create_custom_tourney(message='another')
        assert isinstance(anotehr_tourney, Tourney)
        assert anotehr_tourney.message == 'another'
        assert Tourney.objects.count() == 2

    @pytest.mark.parametrize(
            ('tourney'),
            [lf('tourney_thai_ind'),
             lf('tourney_thai_team')])
    def test_for_tourney_joining(
            self,
            tourney,
            api_client_thailand_pro,
            player_thailand_female_pro
    ):
        GameInvitation.objects.create(
            host=tourney.host,
            invited=player_thailand_female_pro,
            content_object=tourney
        )
        url = reverse(
            'api:tournaments-joining-tournament', args=(tourney.id,))
        assert len(tourney.players) == 0
        request_data = {'team_id': tourney.teams.last().id}
        response = api_client_thailand_pro.post(
            url, request_data, format='json')

        assert player_thailand_female_pro in tourney.players
        assert response.status_code == status.HTTP_200_OK
        assert response.json()['is_joined'] is True
        assert GameInvitation.objects.first() is None

    def test_team_tourney_joining_with_wrong_data(
            self,
            tourney_thai_ind,
            tourney_thai_team,
            api_client_thailand_pro,
            player_thailand_female_pro,
            bulk_create_registered_players
    ):
        url = reverse(
            'api:tournaments-joining-tournament', args=(tourney_thai_team.id,))
        # wrong team_id
        request_data = {'team_id': tourney_thai_ind.teams.last().id}
        response = api_client_thailand_pro.post(
            url, request_data, format='json')
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert player_thailand_female_pro not in tourney_thai_team.players
        # wrong key
        request_data = {'wrong_key': tourney_thai_team.teams.last().id}
        response = api_client_thailand_pro.post(
            url, request_data, format='json')
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert player_thailand_female_pro not in tourney_thai_team.players
        # no invitation
        request_data = {'team_id': tourney_thai_team.teams.last().id}
        response = api_client_thailand_pro.post(
            url, request_data, format='json')
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert player_thailand_female_pro not in tourney_thai_team.players
        # already paticipate
        team = tourney_thai_team.teams.last()
        another_team = tourney_thai_team.teams.first()
        team.players.add(player_thailand_female_pro)
        GameInvitation.objects.create(
            host=tourney_thai_team.host,
            invited=player_thailand_female_pro,
            content_object=tourney_thai_team
        )
        request_data = {'team_id': another_team.id}
        response = api_client_thailand_pro.post(
            url, request_data, format='json')
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert player_thailand_female_pro not in another_team.players.all()
        assert player_thailand_female_pro in team.players.all()
        team.players.clear()
        # team is fullfilled in team tourney
        team.players.set(bulk_create_registered_players[:2])
        assert team.players.count() == 2
        request_data = {'team_id': team.id}
        response = api_client_thailand_pro.post(
            url, request_data, format='json')
        assert response.status_code == status.HTTP_200_OK
        assert response.json()['is_joined'] is False
        assert player_thailand_female_pro not in tourney_thai_team.players

    def test_ind_tourney_joining_with_wrong_data(
            self,
            tourney_thai_ind,
            api_client_thailand_pro,
            player_thailand_female_pro,
            bulk_create_registered_players,
            player_thailand
    ):
        # team is fullfilled in individual tourney
        url = reverse(
            'api:tournaments-joining-tournament', args=(tourney_thai_ind.id,))
        team = tourney_thai_ind.teams.first()
        team.players.set(bulk_create_registered_players)
        team.players.add(player_thailand)
        assert team.players.count() == tourney_thai_ind.max_players
        assert tourney_thai_ind.teams.count() == 1
        GameInvitation.objects.create(
            host=tourney_thai_ind.host,
            invited=player_thailand_female_pro,
            content_object=tourney_thai_ind
        )
        request_data = {'team_id': team.id}
        response = api_client_thailand_pro.post(
            url, request_data, format='json')
        assert response.status_code == status.HTTP_200_OK
        assert response.json()['is_joined'] is False
        assert player_thailand_female_pro not in tourney_thai_ind.players

    def test_for_tourney_invitation_declining(
            self,
            tourney_thai_ind,
            api_client_thailand_pro,
            player_thailand_female_pro,

    ):
        GameInvitation.objects.create(
            host=tourney_thai_ind.host,
            invited=player_thailand_female_pro,
            content_object=tourney_thai_ind
        )
        url = reverse(
            'api:tournaments-delete-invitation',
            args=(tourney_thai_ind.id,)
        )
        assert len(tourney_thai_ind.players) == 0
        assert tourney_thai_ind.event_invites.count() == 1
        response = api_client_thailand_pro.delete(url)
        assert player_thailand_female_pro not in tourney_thai_ind.players
        assert response.status_code == status.HTTP_204_NO_CONTENT
        assert GameInvitation.objects.first() is None

    def test_for_tourney_invitation_declining_wrong_player(
            self,
            tourney_thai_ind,
            api_client_thailand,
            player_thailand_female_pro,

    ):
        GameInvitation.objects.create(
            host=tourney_thai_ind.host,
            invited=player_thailand_female_pro,
            content_object=tourney_thai_ind
        )
        url = reverse(
            'api:tournaments-delete-invitation',
            args=(tourney_thai_ind.id,)
        )
        assert tourney_thai_ind.event_invites.count() == 1
        assert len(tourney_thai_ind.players) == 0
        response = api_client_thailand.delete(url)
        assert player_thailand_female_pro not in tourney_thai_ind.players
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert GameInvitation.objects.first() is not None

    def test_filtering_queryset(
            self,
            tourney_thai_ind,
            create_custom_tourney,
            court_cyprus,
            api_client_thailand,
    ):
        create_custom_tourney(court_id=court_cyprus.id)
        assert Tourney.objects.count() == 2
        response = api_client_thailand.get(
            reverse('api:games-upcoming-games')
        )
        assert len(response.data['tournaments']) == 1
        assert response.data['tournaments'][0][
            'tournament_id'] == tourney_thai_ind.id

    def test_deleting_game_by_host(
            self,
            api_client_thailand,
            tourney_thai_ind,
            tourney_for_args
    ):
        assert Tourney.objects.count() == 1
        response = api_client_thailand.delete(
            reverse('api:tournaments-detail', args=tourney_for_args))
        assert response.status_code == status.HTTP_204_NO_CONTENT
        assert Tourney.objects.count() == 0

    def test_deleting_game_by_non_host(
            self,
            api_client_thailand_pro,
            tourney_thai_ind,
            tourney_for_args
    ):

        assert Tourney.objects.count() == 1
        response = api_client_thailand_pro.delete(
            reverse('api:tournaments-detail', args=tourney_for_args))
        assert response.status_code == status.HTTP_403_FORBIDDEN
        assert Tourney.objects.count() == 1


@pytest.mark.django_db(transaction=False)
class TestTourneySerializers:

    @pytest.mark.parametrize(
        ('tourney'),
        [lf('tourney_thai_ind'),
            lf('tourney_thai_team')])
    def test_tourney_detail_serializer(
            self,
            api_client_thailand,
            player_thailand,
            tourney,
            court_thailand,
            bulk_create_registered_players
    ):
        team = tourney.teams.first()
        team.players.set(bulk_create_registered_players[:2])

        response = api_client_thailand.get(
            reverse(
                'api:tournaments-detail',
                args=(tourney.id,)
            )
        )
        response_data = response.json()

        teams = response_data.pop('teams')
        assert tourney.teams.count() == len(teams)
        assert teams[0]['team_id'] == team.id
        player_ids = [
            player.id for player in bulk_create_registered_players[:2]
        ]
        for player in teams[0]['players']:
            assert player['player_id'] in player_ids

        levels = response_data.pop('levels')
        for level in tourney.player_levels.all():
            assert level.name in levels

        court_data = response_data.pop('court_location')
        assert court_data['longitude'] == court_thailand.location.longitude
        assert court_data['latitude'] == court_thailand.location.latitude
        assert court_data['court_name'] == court_thailand.location.court_name
        assert court_data[
            'location_name'] == court_thailand.location.location_name

        host = response_data.pop('host')
        assert host['player_id'] == player_thailand.id
        assert host['first_name'] == player_thailand.user.first_name
        assert host['last_name'] == player_thailand.user.last_name
        assert host['avatar'] == player_thailand.avatar
        assert host['level'] == player_thailand.rating.grade

        assert (response_data['tournament_id'] ==
                tourney.id)
        assert (response_data['is_individual'] ==
                tourney.is_individual)
        assert (response_data['message'] ==
                tourney.message)
        assert (parse_datetime(response_data['start_time']) ==
                tourney.start_time)
        assert (parse_datetime(response_data['end_time']) ==
                tourney.end_time)
        assert (response_data['gender'] ==
                tourney.gender)
        assert (response_data['price_per_person'] ==
                tourney.price_per_person)
        assert (response_data['currency_type'] ==
                tourney.currency_type.currency_type)
        assert (response_data['payment_type'] ==
                tourney.payment_type)
        assert (response_data['payment_account'] ==
                tourney.payment_account)
        assert (response_data['maximum_players'] ==
                tourney.max_players)
        assert (response_data['maximum_teams'] ==
                tourney.maximum_teams)

    def test_wrong_level_validation_in_tourney_invitation(
            self,
            player_thailand_female_pro,
            api_client_thailand,
            tourney_thai_ind,
            tourney_for_args
    ):
        response = api_client_thailand.post(
            reverse('api:tournaments-invite-players', args=tourney_for_args),
            data={'players': [player_thailand_female_pro.id,]}
        )
        levels = [level.name for level in tourney_thai_ind.player_levels.all()]
        assert player_thailand_female_pro.rating.grade not in levels
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert response.data[0].get('invited')

    def test_level_validation_in_tourney_invitation(
            self,
            player_thailand_female_pro,
            api_client_thailand_pro,
            player_thailand,
            create_custom_tourney
    ):
        tourney = create_custom_tourney(host=player_thailand_female_pro)
        response = api_client_thailand_pro.post(
            reverse('api:tournaments-invite-players', args=(tourney.id,)),
            data={'players': [player_thailand.id,]}
        )
        levels = [level.name for level in tourney.player_levels.all()]
        assert player_thailand.rating.grade in levels
        assert response.status_code == status.HTTP_201_CREATED
        assert tourney.event_invites.filter(invited=player_thailand).exists()

    def test_tourney_short_serializer(
            self,
            tourney_thai_ind,
            tourney_thai_team,
            court_thailand,
            player_thailand
    ):
        tourneys = Tourney.objects.all()
        serializer = TourneyShortSerializer(tourneys, many=True)
        response_data = serializer.data[0]
        assert len(serializer.data) == 2
        court_data = response_data.pop('court_location')
        assert court_data['longitude'] == court_thailand.location.longitude
        assert court_data['latitude'] == court_thailand.location.latitude
        assert court_data['court_name'] == court_thailand.location.court_name
        assert court_data[
            'location_name'] == court_thailand.location.location_name

        host = response_data.pop('host')
        assert host['player_id'] == player_thailand.id
        assert host['first_name'] == player_thailand.user.first_name
        assert host['last_name'] == player_thailand.user.last_name
        assert host['avatar'] == player_thailand.avatar
        assert host['level'] == player_thailand.rating.grade

        assert (response_data['message'] ==
                tourney_thai_ind.message)
        assert (parse_datetime(response_data['start_time']) ==
                tourney_thai_ind.start_time)
        assert (parse_datetime(response_data['end_time']) ==
                tourney_thai_ind.end_time)


@pytest.mark.django_db
class TestTourneyFiltering:

    def test_preview_filtering(
            self,
            api_client_thailand,
            create_custom_tourney,
            tourney_thai_ind
    ):
        nearest_time = now() + timedelta(minutes=1)
        nearest_time = nearest_time.strftime("%Y-%m-%dT%H:%M:%SZ")
        create_custom_tourney(start_time=nearest_time)
        assert Tourney.objects.count() == 2
        response = api_client_thailand.get(reverse('api:games-preview'))
        assert response.json() == {
            'upcoming_game_time': nearest_time,
            'invites': 0
        }

    def test_preview_with_invites(
            self,
            api_client_thailand_pro,
            player_thailand_female_pro,
            tourney_thai_ind,
            create_custom_tourney
    ):
        nearest_time = now() + timedelta(minutes=5)
        nearest_time = nearest_time.strftime("%Y-%m-%dT%H:%M:%SZ")
        create_custom_tourney(
            host=player_thailand_female_pro, start_time=nearest_time)
        GameInvitation.objects.create(
            content_object=tourney_thai_ind,
            host=tourney_thai_ind.host,
            invited=player_thailand_female_pro
        )
        response = api_client_thailand_pro.get(reverse('api:games-preview'))
        assert response.json() == {
            'upcoming_game_time': nearest_time,
            'invites': 1
        }

    def test_my_games_filtering(
            self,
            api_client_thailand,
            tourney_thai_ind,
            create_custom_tourney,
            player_thailand_female_pro
    ):
        create_custom_tourney(host=player_thailand_female_pro)
        assert Tourney.objects.count() == 2
        response = api_client_thailand.get(reverse('api:games-my-games'))
        assert len(response.data['tournaments']) == 1
        assert (response.data['tournaments'][0]['tournament_id'] ==
                tourney_thai_ind.id)

    def test_archive_filtering(
            self,
            tourney_thai_ind,
            create_custom_tourney,
            player_thailand
    ):
        archived = create_custom_tourney(
            end_time=(now() - timedelta(weeks=52)))
        assert Tourney.objects.count() == 2
        result = Tourney.objects.archive_games(player_thailand)
        assert len(result) == 1
        assert result[0].id == archived.id

    def test_invites_filtering(
            self,
            tourney_thai_ind,
            tourney_thai_team,
            player_thailand_female_pro
    ):
        assert Tourney.objects.count() == 2
        tourneys = Tourney.objects.invited_games(player_thailand_female_pro)
        assert not tourneys

        GameInvitation.objects.create(
            content_object=tourney_thai_ind,
            host=tourney_thai_ind.host,
            invited=player_thailand_female_pro
        )
        tourneys = Tourney.objects.invited_games(player_thailand_female_pro)
        assert len(tourneys) == 1
        assert tourneys.first() == tourney_thai_ind

    def test_upcoming_filtering(
            self,
            tourney_thai_ind,
            tourney_thai_team,
            player_thailand_female_pro
    ):
        assert Tourney.objects.count() == 2
        upcomming_tourneys = Tourney.objects.upcoming_games(
            player_thailand_female_pro
        )
        assert not upcomming_tourneys
        team = tourney_thai_team.teams.last()
        team.players.add(player_thailand_female_pro)
        upcomming_games = Tourney.objects.upcoming_games(
            player_thailand_female_pro
        )
        assert len(upcomming_games) == 1
        assert upcomming_games.first() == tourney_thai_team
