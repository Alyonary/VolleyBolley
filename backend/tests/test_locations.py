import pytest
from django.urls import reverse
from rest_framework import status

from apps.locations.models import Country


@pytest.fixture
def setup_test_data():
    """Fixture to set up test data."""
    Country.objects.get_or_create(name='Cyprus')
    Country.objects.get_or_create(name='Thailand')


@pytest.mark.django_db
class TestCountriesAPI:
    """Tests for Countries API endpoint."""

    def test_endpoint_accessibility(self, api_client, setup_test_data):
        """Test that countries endpoint is accessible - status 200."""
        url = reverse('api:countries')
        response = api_client.get(url)

        assert response.status_code == status.HTTP_200_OK

    def test_response_structure(self, api_client, setup_test_data):
        """Test response has correct JSON structure."""
        url = reverse('api:countries')
        response = api_client.get(url)

        assert response.status_code == status.HTTP_200_OK

        assert 'countries' in response.data
        assert isinstance(response.data['countries'], list)

        if response.data['countries']:
            country = response.data['countries'][0]
            assert 'country_id' in country
            assert 'country_name' in country
            assert 'cities' in country
            assert isinstance(country['cities'], list)

            if country['cities']:
                city = country['cities'][0]
                assert 'city_id' in city
                assert 'city_name' in city

    def test_empty_database(self, api_client):
        """Test API with empty database."""
        # Очистка базы данных только для этого теста
        Country.objects.all().delete()

        url = reverse('api:countries')
        response = api_client.get(url)

        assert response.status_code == status.HTTP_200_OK
        assert response.data['countries'] == []

        Country.objects.get_or_create(name='Cyprus')
        Country.objects.get_or_create(name='Thailand')

    def test_country_without_cities(self, api_client, setup_test_data):
        """Test country that has no cities."""
        Country.objects.create(name='Empty Country')

        url = reverse('api:countries')
        response = api_client.get(url)

        assert response.status_code == status.HTTP_200_OK

        countries_data = response.data['countries']
        empty_country = next(
            (
                c
                for c in countries_data
                if c['country_name'] == 'Empty Country'
            ),
            None,
        )
        assert empty_country is not None
        assert empty_country['cities'] == []

    def test_http_methods(self, api_client, setup_test_data):
        """Test that only GET method is allowed."""
        url = reverse('api:countries')

        response = api_client.get(url)
        assert response.status_code == status.HTTP_200_OK

        response = api_client.post(url, {})
        assert response.status_code == status.HTTP_405_METHOD_NOT_ALLOWED

        response = api_client.put(url, {})
        assert response.status_code == status.HTTP_405_METHOD_NOT_ALLOWED

        response = api_client.patch(url, {})
        assert response.status_code == status.HTTP_405_METHOD_NOT_ALLOWED

        response = api_client.delete(url)
        assert response.status_code == status.HTTP_405_METHOD_NOT_ALLOWED

    def test_countries_alphabetical_sorting(self, api_client, setup_test_data):
        """Test that countries are sorted alphabetically."""
        Country.objects.create(name='Vietnam')
        Country.objects.create(name='Malaysia')

        url = reverse('api:countries')
        response = api_client.get(url)

        assert response.status_code == status.HTTP_200_OK

        countries_data = response.data['countries']
        country_names = [c['country_name'] for c in countries_data]

        expected_order = ['Cyprus', 'Malaysia', 'Thailand', 'Vietnam']
        assert country_names == expected_order

        assert country_names == sorted(country_names)
