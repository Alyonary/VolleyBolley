import random

import pytest
from django.apps import apps
from django.db import IntegrityError
from django.urls import reverse
from rest_framework import status

from apps.core.models import FAQ
from apps.core.signals import load_faq


@pytest.mark.django_db
class TestFAQModel:
    @pytest.fixture(autouse=True)
    def setup(self):
        self.faq1 = FAQ.objects.create(content="FAQ 1", is_active=False)
        self.faq2 = FAQ.objects.create(content="FAQ 2", is_active=False)

    def test_create_faq(self):
        faq = FAQ.objects.create(content="New FAQ", is_active=False)
        assert faq.content == "New FAQ"
        assert not faq.is_active
        assert faq.name.startswith("faq ")  # name is auto-generated

    def test_create_faq_with_name(self):
        faq = FAQ.objects.create(
            content="Named FAQ",
            is_active=False,
            name="custom_name"
        )
        assert faq.name == "custom_name"

    def test_activate_faq_deactivates_others(self):
        self.faq1.is_active = True
        self.faq1.save()
        self.faq2.refresh_from_db()
        assert self.faq1.is_active
        assert not self.faq2.is_active

    def test_get_active(self):
        self.faq2.is_active = True
        self.faq2.save()
        active_faq = FAQ.get_active()
        assert active_faq == self.faq2

    def test_signal_deactivate_other_faqs(self):
        self.faq1.is_active = True
        self.faq1.save()
        self.faq2.is_active = True
        self.faq2.save()
        self.faq1.refresh_from_db()
        self.faq2.refresh_from_db()
        assert self.faq2.is_active
        assert not self.faq1.is_active

    def test_create_multiple_active_faqs(self):
        FAQ.objects.all().delete()
        faqs_quantity = random.randint(5, 10)
        for i in range(faqs_quantity):
            FAQ.objects.create(content=f"FAQ {i}", is_active=True)
        assert FAQ.objects.filter(is_active=True).count() == 1
        assert FAQ.objects.all().count() == faqs_quantity

    def test_signal_load_faq_after_migrations(self):
        FAQ.objects.all().delete()
        app_config = apps.get_app_config('core')
        load_faq(sender=app_config)
        faq = FAQ.objects.filter(is_active=True).first()

        assert faq is not None
        assert faq.content
        assert faq.is_active
        assert faq.name

    def test_unique_name_constraint(self):
        """
        Test that FAQ name must be unique.
        """
        FAQ.objects.create(
            content="Unique FAQ",
            is_active=False,
            name="unique_name"
        )
        with pytest.raises(IntegrityError):
            FAQ.objects.create(
                content="Another FAQ",
                is_active=False,
                name="unique_name"
            )

    def test_auto_generated_name_is_unique(self):
        """
        Test that auto-generated FAQ names are unique.
        """
        FAQ.objects.all().delete()
        faq1 = FAQ.objects.create(content="Auto 1", is_active=False)
        faq2 = FAQ.objects.create(content="Auto 2", is_active=False)
        assert faq1.name != faq2.name
        assert faq1.name.startswith("faq ")
        assert faq2.name.startswith("faq ")

@pytest.mark.django_db
def test_faq_api_returns_active_faq(auth_api_client_registered_player):
    faq = FAQ.get_active()
    if not faq:
        faq = FAQ.objects.create(content="API FAQ", is_active=True)
    else:
        faq.content = "API FAQ"
        faq.is_active = True
        faq.save()
    url = reverse("api:faq")
    response = auth_api_client_registered_player.get(url)
    assert response.status_code == status.HTTP_200_OK
    assert response.data["faq"] == faq.content

@pytest.mark.django_db
def test_faq_api_returns_404_if_no_active_faq(
    auth_api_client_registered_player
):
    FAQ.objects.all().delete()
    url = reverse("api:faq")
    response = auth_api_client_registered_player.get(url)
    assert response.status_code == status.HTTP_404_NOT_FOUND
    assert "No active FAQ available." in response.data["faq"]

@pytest.mark.django_db
def test_faq_api_permission_denied(api_client):
    url = reverse("api:faq")
    response = api_client.get(url)
    assert response.status_code == status.HTTP_401_UNAUTHORIZED

@pytest.mark.django_db
def test_faq_api_for_unregistered_player(
    auth_api_client_with_not_registered_player
):
    url = reverse("api:faq")
    response = auth_api_client_with_not_registered_player.get(url)
    assert response.status_code == status.HTTP_403_FORBIDDEN

