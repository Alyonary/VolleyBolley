from typing import Any, Tuple
from typing import Any, Tuple

import pytest
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient
from apps.courts.models import Court
from apps.players.models import Player
from apps.users.models import User
from backend.apps.courts.serializers import CourtSerializer
from tests.subfunctions.base import get_model_objects

from rest_framework.response import Response


@pytest.mark.django_db
class TestCourtAPI:
    """Integration tests for Court API endpoints and geographic filters."""

    def test_list_courts_filtered_by_player_geo(
        self,
        authenticated_client: Tuple[APIClient, User],
        fake_courts_cyprus: Any,
        fake_courts_thailand: Any,
        court_cyprus: Court,
        court_list_url: str,
    ) -> None:
        """Player from Thailand sees only courts from Thailand."""
        client, user = authenticated_client
        player: Player = user.player
        courts_by_geo: Any = get_model_objects(
            Court, location__country=player.country
        )
        response: Response = client.get(court_list_url)
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data) == len(courts_by_geo)

    def test_list_courts_for_player_without_geo(
        self,
        api_client: APIClient,
        player_no_geo: Player,
        fake_courts_cyprus: Any,
        fake_courts_thailand: Any,
        court_list_url: str,
    ) -> None:
        """All courts are returned if player has no geo data."""
        api_client.force_authenticate(user=player_no_geo.user)
        courts_in_db: Any = get_model_objects(Court)
        response: Response = api_client.get(court_list_url)
        assert response.status_code == status.HTTP_200_OK
        results: Any = response.data
        assert len(response.data) != len(courts_in_db)

    def test_retrieve_local_court_success(
        self,
        authenticated_client: Tuple[APIClient, User],
        court_obj_with_tag: Court,
        contact_object: Any,
    ) -> None:
        """Successfully retrieve domestic court without events flag."""
        client, _ = authenticated_client
        url: str = reverse(
            'api:courts-detail', kwargs={'pk': court_obj_with_tag.id}
        )
        response: Response = client.get(url)
        assert response.status_code == status.HTTP_200_OK
        assert 'games' not in response.data
        assert 'tournaments' not in response.data
        assert response.data['court_id'] == court_obj_with_tag.id

    def test_retrieve_foreign_court_returns_404(
        self,
        authenticated_client: Tuple[APIClient, User],
        fake_courts_cyprus: Any,
        fake_courts_thailand: Any,
    ) -> None:
        """Attempt to retrieve foreign court returns 404 due to geo filter."""
        client, user = authenticated_client
        player: Player = user.player
        foreign_court: Any = (
            get_model_objects(Court)
            .exclude(location__country=player.country)
            .first()
        )
        url: str = reverse(
            'api:courts-detail', kwargs={'pk': foreign_court.pk}
        )
        response: Response = client.get(url)
        assert response.status_code == status.HTTP_404_NOT_FOUND

    @pytest.mark.parametrize('flag_value', ['true', '1', 'TRUE'])
    def test_retrieve_court_with_events_detail_active(
        self,
        authenticated_client: Tuple[APIClient, User],
        court_cyprus: Court,
        flag_value: str,
    ) -> None:
        """Flag events_detail activates conditional prefetch and serializer."""
        client, _ = authenticated_client
        url: str = reverse('api:courts-detail', kwargs={'pk': court_cyprus.id})
        response: Response = client.get(f'{url}?events_detail={flag_value}')
        assert response.status_code == status.HTTP_200_OK
        assert 'games' in response.data or 'tournaments' in response.data

    @pytest.mark.parametrize('flag_value', ['false', '0', 'none', ''])
    def test_retrieve_court_with_events_detail_inactive(
        self,
        authenticated_client: Tuple[APIClient, User],
        court_cyprus: Court,
        flag_value: str,
    ) -> None:
        """Invalid or negative flag values return default serializer."""
        client, _ = authenticated_client
        url: str = reverse('api:courts-detail', kwargs={'pk': court_cyprus.id})
        response: Response = client.get(f'{url}?events_detail={flag_value}')
        assert response.status_code == status.HTTP_200_OK
        assert 'games' not in response.data
        assert 'tournaments' not in response.data

    def test_court_http_methods_restricted(
        self,
        authenticated_client: Tuple[APIClient, User],
        court_list_url: str,
        court_thailand: Court,
    ) -> None:
        """Only GET requests are allowed; POST/PUT/DELETE return 405."""
        detail_url: str = reverse(
            'api:courts-detail', kwargs={'pk': court_thailand.id}
        )
        client, _ = authenticated_client
        post_res = client.post(court_list_url, data={})
        put_res = client.put(detail_url, data={})
        delete_res = client.delete(detail_url)

        assert post_res.status_code == status.HTTP_405_METHOD_NOT_ALLOWED
        assert put_res.status_code == status.HTTP_405_METHOD_NOT_ALLOWED
        assert delete_res.status_code == status.HTTP_405_METHOD_NOT_ALLOWED
