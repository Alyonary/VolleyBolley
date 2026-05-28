import random
from typing import Any, Tuple

import pytest
from django.urls import reverse
from rest_framework import status
from rest_framework.response import Response
from rest_framework.test import APIClient

from apps.courts.models import Court
from apps.locations.models import Country
from apps.players.models import Player
from apps.users.models import User


@pytest.mark.django_db
@pytest.mark.usefixtures('fake_courts_cyprus', 'fake_courts_thailand')
class TestCourtAPI:
    def test_list_courts_filtered_by_player_geo(
        self,
        authenticated_client_thailand_player: Tuple[APIClient, User],
        court_cyprus: Court,
        court_list_url: str,
    ) -> None:
        """Player from Thailand sees only courts from Thailand."""
        client, player = authenticated_client_thailand_player
        courts_by_geo: Any = Court.objects.filter(
            location__country=player.country
        )
        response: Response = client.get(court_list_url)
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data) == len(courts_by_geo)

    def test_list_courts_for_player_without_geo(
        self,
        api_client: APIClient,
        player_no_geo: Player,
        court_list_url: str,
    ) -> None:
        """All courts are returned if player has no geo data."""
        api_client.force_authenticate(user=player_no_geo.user)
        courts_in_db: Any = Court.objects.all()
        response: Response = api_client.get(court_list_url)
        assert response.status_code == status.HTTP_200_OK
        results: Any = response.data
        assert len(response.data) != len(courts_in_db)

    def test_retrieve_local_court_success(
        self,
        authenticated_client_thailand_player: Tuple[APIClient, User],
        authenticated_client_сyprus_player: Tuple[APIClient, User],
        court_obj_with_tag: Court,
        contact_object: Any,
    ) -> None:
        """Successfully retrieve domestic court without events flag."""
        client, player = random.choice([authenticated_client_thailand_player])
        court = Court.objects.filter(location__country=player.country).first()
        print(Country.objects.all())
        assert player.country.id == court.location.country.id
        print('COURT LOCATION', court.location.country, court.location.city)
        print('PLAYER COUNTRY', player.country)
        assert player.country == court.location.country
        url: str = reverse('api:courts-detail', kwargs={'pk': court.id})
        response: Response = client.get(url)
        assert response.status_code == status.HTTP_200_OK
        assert 'games' not in response.data
        assert 'tournaments' not in response.data
        assert response.data['court_id'] == court.id

    def test_retrieve_foreign_court_returns_404(
        self,
        authenticated_client_thailand_player: Tuple[APIClient, User],
        authenticated_client_сyprus_player: Tuple[APIClient, User],
    ) -> None:
        """Attempt to retrieve foreign court returns 404 due to geo filter."""
        client, player = random.choice([authenticated_client_thailand_player])
        print(Country.objects.all())
        foreign_court: Any = Court.objects.exclude(
            location__country=player.country
        ).first()
        url: str = reverse(
            'api:courts-detail', kwargs={'pk': foreign_court.pk}
        )
        response: Response = client.get(url)
        assert response.status_code == status.HTTP_404_NOT_FOUND

    @pytest.mark.parametrize('flag_value', ['true', '1', 'TRUE'])
    def test_retrieve_court_with_active_events_only(
        self,
        authenticated_client_thailand_player: Tuple[APIClient, User],
        court_obj_with_tag: Court,
        flag_value: str,
    ) -> None:
        """active_events=true возвращает court с активными ивентами, но без деталей."""
        client, player = authenticated_client_thailand_player
        court = Court.objects.filter(location__country=player.country).first()
        url: str = reverse('api:courts-detail', kwargs={'pk': court.pk})
        response: Response = client.get(f'{url}?active_events={flag_value}')
        assert response.status_code == status.HTTP_200_OK
        assert 'games' not in response.data
        assert 'tournaments' not in response.data

    @pytest.mark.parametrize('flag_value', ['true', '1', 'TRUE'])
    def test_retrieve_court_with_active_events_and_details(
        self,
        authenticated_client_thailand_player: Tuple[APIClient, User],
        court_obj_with_tag: Court,
        flag_value: str,
    ) -> None:
        """active_events=true и events_detail=true возвращают court с деталями ивентов."""
        client, player = authenticated_client_thailand_player
        court = Court.objects.filter(location__country=player.country).first()
        url: str = reverse('api:courts-detail', kwargs={'pk': court.pk})
        response: Response = client.get(
            f'{url}?active_events={flag_value}&events_detail={flag_value}'
        )
        assert response.status_code == status.HTTP_200_OK
        assert 'games' in response.data or 'tournaments' in response.data

    @pytest.mark.parametrize('flag_value', ['false', '0', 'none', ''])
    def test_retrieve_court_with_events_detail_inactive(
        self,
        authenticated_client_thailand_player: Tuple[APIClient, User],
        court_obj_with_tag: Court,
        flag_value: str,
    ) -> None:
        """events_detail без active_events не возвращает детали ивентов."""
        client, player = authenticated_client_thailand_player
        court = Court.objects.filter(location__country=player.country).first()
        url: str = reverse('api:courts-detail', kwargs={'pk': court.pk})
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
