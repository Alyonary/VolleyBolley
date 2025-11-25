import pytest
from rest_framework.test import APIClient
from rest_framework.reverse import reverse
from apps.core.models import CurrencyType


@pytest.mark.django_db
class TestCurrenciesView:
    """Test suite for the CurrenciesView API."""

    @pytest.fixture(autouse=True)
    def setup(self, api_client: APIClient):
        """Fixture to set up test data."""
        self.client = api_client
        self.url = reverse('api:currencies')
        self.data_structure = {
            'currencies': [
                {
                    'currency_id': int,
                    'currency_type': str,
                    'currency_name': str,
                    'country': {
                        'country_id': (int, type(None)),
                    },
                }
            ]
        }

    def test_get_currencies_success(self):
        """Test successful retrieval of currencies."""
        response = self.client.get(self.url)
        assert response.status_code == 200
        assert 'currencies' in response.data

    def test_currencies_data_structure(self):
        """Test the structure of the returned currencies data."""
        response = self.client.get(self.url)
        assert response.status_code == 200
        assert isinstance(response.data, dict)
        assert 'currencies' in response.data
        assert isinstance(response.data['currencies'], list)

        for currency in response.data['currencies']:
            assert isinstance(currency, dict)
            for key, value_type in self.data_structure['currencies'][0].items():
                assert key in currency
                if isinstance(value_type, dict):
                    assert isinstance(currency[key], dict)
                    for sub_key, sub_value_type in value_type.items():
                        assert sub_key in currency[key]
                        assert isinstance(
                            currency[key][sub_key], sub_value_type
                        )
                else:
                    assert isinstance(currency[key], value_type)

    def test_post_not_allowed(self):
        """Test that POST method is not allowed."""
        response = self.client.post(self.url, data={})
        assert response.status_code == 405 

    def test_put_not_allowed(self):
        """Test that PUT method is not allowed."""
        response = self.client.put(self.url, data={})
        assert response.status_code == 405

    def test_delete_not_allowed(self):
        """Test that DELETE method is not allowed."""
        response = self.client.delete(self.url)
        assert response.status_code == 405

    def test_patch_not_allowed(self):
        """Test that PATCH method is not allowed."""
        response = self.client.patch(self.url, data={})
        assert response.status_code == 405
