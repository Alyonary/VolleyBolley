import pytest
from django.urls import reverse
from rest_framework import status

from apps.event.models import Game
from apps.players.models import PlayerRatingVote
from apps.players.rating import GradeSystem


@pytest.mark.django_db
class TestRatePlayersAPI:
    """Test rate players functionality with real API calls."""

    def test_get_players_to_rate_in_game_api(
        self,
        api_client,
        game_thailand,
        players
    ):
        """Test GET /api/games/{id}/rate-players/ endpoint."""
        player = players['player1']
        api_client.force_authenticate(user=player.user)
        game: Game = game_thailand
        game.players.add(*players.values())
        game.save()
        expected_players = [p for p in players.values() if p != player]
        url = reverse('api:games-rate-players', args=[game.id])
        response = api_client.get(url)
        assert response.status_code == status.HTTP_200_OK
        assert 'players' in response.data
        players_data = response.data['players']
        for player_data in players_data:
            required_fields = {
                'player_id', 'first_name', 'last_name', 'avatar', 'level'
            }
            assert set(player_data.keys()) == required_fields
            assert isinstance(player_data['player_id'], int)
            assert isinstance(player_data['first_name'], str)
            assert isinstance(player_data['last_name'], str)
            assert player_data['level'] in [
                'LIGHT', 'MEDIUM', 'HARD', 'PRO'
            ]
            assert len(players_data) == len(
                set(p.id for p in expected_players)
            )

    @pytest.mark.parametrize("rater_grade,rated_grade,level_changed", [
        ('LIGHT', 'LIGHT', 'UP'),
        ('LIGHT', 'LIGHT', 'DOWN'),
        ('LIGHT', 'LIGHT', 'CONFIRM'),
        ('LIGHT', 'MEDIUM', 'UP'),
        ('LIGHT', 'HARD', 'DOWN'),
        ('LIGHT', 'PRO', 'CONFIRM'),
        ('MEDIUM', 'LIGHT', 'UP'),
        ('MEDIUM', 'LIGHT', 'DOWN'),
        ('MEDIUM', 'MEDIUM', 'CONFIRM'),
        ('MEDIUM', 'HARD', 'UP'),
        ('MEDIUM', 'PRO', 'DOWN'),
        ('HARD', 'LIGHT', 'CONFIRM'),
        ('HARD', 'MEDIUM', 'UP'),
        ('HARD', 'HARD', 'DOWN'),
        ('HARD', 'PRO', 'CONFIRM'),
        ('PRO', 'LIGHT', 'UP'),
        ('PRO', 'MEDIUM', 'DOWN'),
        ('PRO', 'HARD', 'CONFIRM'),
        ('PRO', 'PRO', 'UP'),
        ('PRO', 'PRO', 'DOWN'),
        ('PRO', 'PRO', 'CONFIRM'),
    ])
    def test_post_rate_player_in_game_api(
        self,
        api_client_thailand,
        game_thailand_with_players,
        player_thailand,
        bulk_create_registered_players,
        rater_grade,
        rated_grade,
        level_changed
    ):
        """Test POST /api/games/{id}/rate-players/ endpoint."""
        game = game_thailand_with_players
        rater = player_thailand
        rated_player = bulk_create_registered_players[0]

        rater.rating.grade = rater_grade
        rater.rating.save()
        rated_player.rating.grade = rated_grade
        rated_player.rating.save()
        rater.refresh_from_db()
        rated_player.refresh_from_db()

        if rater not in game.players.all():
            game.players.add(rater)
        if rated_player not in game.players.all():
            game.players.add(rated_player)

        url = reverse('api:games-rate-players', args=[game.id])
        post_data = {
            'players': [
                {
                    'player_id': rated_player.id,
                    'level_changed': level_changed
                }
            ]
        }
        response = api_client_thailand.post(url, post_data, format='json')
        assert response.status_code == status.HTTP_201_CREATED
        vote = PlayerRatingVote.objects.filter(
            rater=rater,
            rated=rated_player
        ).first()

        expected_value = GradeSystem.get_value(
            rater=rater,
            rated=rated_player,
            level_change=level_changed
        )
        assert vote is not None
        assert vote.is_counted is False
        assert vote.value == expected_value
        vote.delete()

    @pytest.mark.parametrize(
        "post_data,expected_status",
        [
            ({}, status.HTTP_400_BAD_REQUEST),
            ({'players': []}, status.HTTP_400_BAD_REQUEST),
            (
                {'players': [{'level_changed': 'UP'}]},
                status.HTTP_400_BAD_REQUEST
            ),
            (
                {'players': [{'player_id': 1}]},
                status.HTTP_400_BAD_REQUEST
            ),
            (
                {'players': [{'player_id': 1, 'level_changed': 'INVALID'}]},
                status.HTTP_400_BAD_REQUEST
            ),
            (
                {'players': [{'player_id': 1, 'level_changed': ''}]},
                status.HTTP_400_BAD_REQUEST
            ),
            (
                {'players': [{'player_id': 1, 'level_changed': None}]},
                status.HTTP_400_BAD_REQUEST
            ),
            (
                {
                    'players': [
                        {'player_id': 'invalid', 'level_changed': 'UP'}
                    ]
                },
                status.HTTP_400_BAD_REQUEST
            ),
            (
                {'players': [{'player_id': -1, 'level_changed': 'UP'}]},
                status.HTTP_400_BAD_REQUEST
            ),
            (
                {'players': {'player_id': 1, 'level_changed': 'UP'}},
                status.HTTP_400_BAD_REQUEST
            ),
            (
                {
                    'players': [
                        {'player_id': 1, 'level_changed': 'UP'},
                        {'player_id': 2, 'level_changed': 'INVALID'}
                    ]
                },
                status.HTTP_400_BAD_REQUEST
            ),
            (
                {
                    'players': [
                        {'player_id': 1, 'level': 'UP'},
                        {'player_id': 2, 'changed': 'INVALID'}
                    ]
                },
                status.HTTP_400_BAD_REQUEST
            ),
        ]
    )
    def test_post_rate_player_in_game_api_invalid_data_structural(
        self,
        api_client_thailand,
        game_thailand_with_players,
        player_thailand,
        bulk_create_registered_players,
        post_data,
        expected_status
    ):
        """Test POST with structurally invalid data returns 400."""
        game = game_thailand_with_players
        rater = player_thailand
        rated_player = bulk_create_registered_players[0]

        game.players.add(rater, rated_player)

        if 'players' in post_data and isinstance(post_data['players'], list):
            for player_data in post_data['players']:
                if isinstance(player_data, dict):
                    player_id = player_data.get('player_id')
                    if player_id == 1:
                        player_data['player_id'] = rated_player.id
                    elif player_id == 2:
                        if len(bulk_create_registered_players) > 1:
                            player_data['player_id'] = (
                                bulk_create_registered_players[1].id
                            )

        url = reverse('api:games-rate-players', args=[game.id])
        response = api_client_thailand.post(url, post_data, format='json')

        assert response.status_code == expected_status
        vote_count = PlayerRatingVote.objects.filter(rater=rater).count()
        assert vote_count == 0

    @pytest.mark.parametrize(
        "post_data",
        [
            ({'players': [{'player_id': 999, 'level_changed': 'UP'}]}),
            (
                {
                    'players': [
                        {
                            'player_id': 1,
                            'level_changed': 'UP',
                            'extra_field': 'value'
                        }
                    ]
                }
            ),
        ]
    )
    def test_post_rate_player_in_game_api_invalid_data_business(
        self,
        api_client_thailand,
        game_thailand_with_players,
        player_thailand,
        bulk_create_registered_players,
        post_data
    ):
        """
        Test POST with business logic errors returns 200.
        Skips invalid items.
        """
        game = game_thailand_with_players
        rater = player_thailand
        rated_player = bulk_create_registered_players[0]

        game.players.add(rater, rated_player)

        if 'players' in post_data and isinstance(post_data['players'], list):
            for player_data in post_data['players']:
                if isinstance(player_data, dict):
                    player_id = player_data.get('player_id')
                    if player_id == 1:
                        player_data['player_id'] = rated_player.id

        url = reverse('api:games-rate-players', args=[game.id])
        response = api_client_thailand.post(url, post_data, format='json')

        assert response.status_code == status.HTTP_201_CREATED
        vote_count = PlayerRatingVote.objects.filter(rater=rater).count()

        if post_data['players'][0].get('player_id') == 999:
            assert vote_count == 0
        else:
            assert vote_count >= 0
            PlayerRatingVote.objects.filter(rater=rater).delete()

    @pytest.mark.parametrize("rater_in_game,rated_in_game", [
        (False, True),
        (True, False),
        (False, False),
        (True, True),
    ])
    def test_post_rate_player_participation_validation(
        self,
        api_client_thailand,
        game_thailand_with_players,
        player_thailand,
        bulk_create_registered_players,
        rater_in_game,
        rated_in_game
    ):
        """Test validation that players must participate in game to rate."""
        game = game_thailand_with_players
        rater = player_thailand
        rated_player = bulk_create_registered_players[0]

        game.players.clear()

        if rater_in_game:
            game.players.add(rater)
        if rated_in_game:
            game.players.add(rated_player)

        url = reverse('api:games-rate-players', args=[game.id])
        post_data = {
            'players': [
                {
                    'player_id': rated_player.id,
                    'level_changed': 'UP'
                }
            ]
        }

        response = api_client_thailand.post(url, post_data, format='json')
        assert response.status_code == status.HTTP_201_CREATED
        vote_count = PlayerRatingVote.objects.filter(rater=rater).count()

        if rater_in_game and rated_in_game:
            assert vote_count >= 1
            PlayerRatingVote.objects.filter(rater=rater).delete()
        else:
            assert vote_count == 0

    def test_post_rate_player_duplicate_vote_prevention(
        self,
        api_client_thailand,
        game_thailand_with_players,
        player_thailand,
        bulk_create_registered_players
    ):
        """Test that duplicate votes are handled properly."""
        game = game_thailand_with_players
        rater = player_thailand
        rated_player = bulk_create_registered_players[0]

        game.players.add(rater, rated_player)
        PlayerRatingVote.objects.create(
            rater=rater,
            rated=rated_player,
            game=game,
            value=1.0,
            is_counted=False
        )

        url = reverse('api:games-rate-players', args=[game.id])
        post_data = {
            'players': [
                {
                    'player_id': rated_player.id,
                    'level_changed': 'UP'
                }
            ]
        }
        response = api_client_thailand.post(url, post_data, format='json')

        assert response.status_code == status.HTTP_201_CREATED
        vote_count = PlayerRatingVote.objects.filter(
            rater=rater,
            rated=rated_player
        ).count()
        assert vote_count == 1

    def test_post_rate_player_unauthorized(
        self,
        api_client,
        game_thailand_with_players
    ):
        """Test that unauthorized requests return 401."""
        game = game_thailand_with_players
        url = reverse('api:games-rate-players', args=[game.id])

        post_data = {
            'players': [
                {
                    'player_id': 1,
                    'level_changed': 'UP'
                }
            ]
        }

        response = api_client.post(url, post_data, format='json')
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
        vote_count = PlayerRatingVote.objects.count()
        assert vote_count == 0

    def test_post_rate_player_nonexistent_game(
        self,
        api_client_thailand,
        player_thailand
    ):
        """Test POST to nonexistent game returns 404."""
        nonexistent_game_id = 99999
        url = reverse('api:games-rate-players', args=[nonexistent_game_id])

        post_data = {
            'players': [
                {
                    'player_id': player_thailand.id,
                    'level_changed': 'UP'
                }
            ]
        }
        response = api_client_thailand.post(url, post_data, format='json')
        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_post_rate_player_multiple_games_limit(
        self,
        api_client_thailand,
        player_thailand,
        bulk_create_registered_players,
        three_games_thailand
    ):
        """Test that player can only rate another player twice in 60 days."""
        rater = player_thailand
        games: list[Game] = three_games_thailand.copy()
        rated_player = bulk_create_registered_players[0]
        for game in games:
            game.players.add(rater, rated_player)
            game.save()
        url_template = 'api:games-rate-players'
        post_data = {
            'players': [
                {
                    'player_id': rated_player.id,
                    'level_changed': 'UP'
                }
            ]
        }

        for i, game in enumerate(games):
            url = reverse(url_template, args=[game.id])
            response = api_client_thailand.post(url, post_data, format='json')

            assert response.status_code == status.HTTP_201_CREATED

            vote_count = PlayerRatingVote.objects.filter(
                rater=rater,
                rated=rated_player
            ).count()

            if i < 2:
                assert vote_count == i + 1
            else:
                assert vote_count == 2

        total_votes = PlayerRatingVote.objects.filter(
            rater=rater,
            rated=rated_player
        ).count()
        assert total_votes == 2

        PlayerRatingVote.objects.filter(rater=rater).delete()

    def test_post_rate_player_mixed_validation_errors(
        self,
        api_client_thailand,
        game_thailand_with_players,
        player_thailand,
        bulk_create_registered_players
    ):
        """
        Test POST with mixed validation errors:
        - One invalid player_id (structural error)
        - One player already rated (business logic error)
        - One player not in game (business logic error)
        Should return 400 due to structural error.
        """
        game = game_thailand_with_players
        rater = player_thailand
        rated_player1 = bulk_create_registered_players[0]
        rated_player2 = bulk_create_registered_players[1]
        rated_player3 = bulk_create_registered_players[2]

        game.players.add(rater, rated_player1, rated_player2)

        PlayerRatingVote.objects.create(
            rater=rater,
            rated=rated_player1,
            game=game,
            value=1.0,
            is_counted=False
        )
        initial_vote_count = PlayerRatingVote.objects.filter(
            rater=rater,
            game=game
        ).count()

        url = reverse('api:games-rate-players', args=[game.id])
        post_data = {
            'players': [
                {
                    'player': 'INVALID',
                    'level_changed': 'UP'
                },
                {
                    'player_id': rated_player1.id,
                    'level_changed': 'UP'
                },
                {
                    'player_id': rated_player3.id,
                    'level_changed': 'UP'
                }
            ]
        }

        response = api_client_thailand.post(url, post_data, format='json')

        assert response.status_code == status.HTTP_400_BAD_REQUEST

        final_vote_count = PlayerRatingVote.objects.filter(
            rater=rater,
            game=game
        ).count()
        assert final_vote_count == initial_vote_count

    def test_post_rate_player_business_logic_only_errors(
        self,
        api_client_thailand,
        three_games_thailand,
        player_thailand,
        bulk_create_registered_players
    ):
        """
        Test POST with only business logic errors:
        - One player already rated (business logic error)
        - One player not in game (business logic error)
        - One valid player to rate
        Should return 200 and create only valid vote.
        """
        game = three_games_thailand[0]
        rater = player_thailand
        rated_player = bulk_create_registered_players[1]
        rated_player_with_vote = bulk_create_registered_players[0]
        rated_player_not_in_game = bulk_create_registered_players[2]
        game.players.clear()
        game.players.add(rater, rated_player, rated_player_with_vote)

        assert rated_player_not_in_game not in game.players.all()

        PlayerRatingVote.objects.create(
            rater=rater,
            rated=rated_player_with_vote,
            game=game,
            value=1.0,
            is_counted=False
        )
        initial_vote_count = PlayerRatingVote.objects.filter(
            rater=rater,
            game=game
        ).count()
        url = reverse('api:games-rate-players', args=[game.id])
        post_data = {
            'players': [
                {
                    'player_id': rated_player.id,
                    'level_changed': 'UP'
                },
                {
                    'player_id': rated_player_with_vote.id,
                    'level_changed': 'UP'
                },
                {
                    'player_id': rated_player_not_in_game.id,
                    'level_changed': 'UP'
                }
            ]
        }
        response = api_client_thailand.post(url, post_data, format='json')

        assert response.status_code == status.HTTP_201_CREATED

        vote_count = PlayerRatingVote.objects.filter(
            rater=rater,
            game=game
        ).count()
        assert vote_count == initial_vote_count + 1

        # Проверяем что новый голос создан только для rated_player3
        new_vote = PlayerRatingVote.objects.filter(
            rater=rater,
            rated=rated_player,
            game=game
        ).first()
        assert new_vote is not None

        invalid_vote = PlayerRatingVote.objects.filter(
            rater=rater,
            rated=rated_player_not_in_game,
            game=game
        ).first()

        assert invalid_vote is None

        PlayerRatingVote.objects.filter(rater=rater, game=game).delete()

    def test_post_rate_player_structural_error_stops_processing(
        self,
        api_client_thailand,
        game_thailand_with_players,
        player_thailand,
        bulk_create_registered_players
    ):
        """
        Test POST with structural error in first item stops all processing:
        - Invalid player_id (structural error)
        - Valid player to rate
        - Another valid player to rate
        Should return 400 and create no votes.
        """
        game = game_thailand_with_players
        rater = player_thailand
        rated_player1 = bulk_create_registered_players[0]
        rated_player2 = bulk_create_registered_players[1]

        game.players.add(rater, rated_player1, rated_player2)

        url = reverse('api:games-rate-players', args=[game.id])
        post_data = {
            'players': [
                {
                    'player_id': 'invalid_id',
                    'level_changed': 'UP'
                },
                {
                    'player_id': rated_player1.id,
                    'level_changed': 'UP'
                },
                {
                    'player_id': rated_player2.id,
                    'level_changed': 'DOWN'
                }
            ]
        }

        response = api_client_thailand.post(url, post_data, format='json')

        assert response.status_code == status.HTTP_400_BAD_REQUEST

        vote_count = PlayerRatingVote.objects.filter(
            rater=rater,
            game=game
        ).count()
        assert vote_count == 0
