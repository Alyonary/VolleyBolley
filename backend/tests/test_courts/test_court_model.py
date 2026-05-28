from typing import Any, Dict

import pytest
from django.db import transaction
from django.db.utils import IntegrityError

from apps.core.models import Contact, Tag
from apps.courts.models import Court, CourtLocation


@pytest.mark.django_db
class TestLocationTagModel:
    def test_create_location(
        self,
        location_for_court_data: Dict[str, Any],
        country_thailand: Any,
        city_in_thailand: Any,
    ) -> None:
        count_before: int = CourtLocation.objects.count()

        location_for_court_data.update(
            {'country': country_thailand, 'city': city_in_thailand}
        )
        location: CourtLocation = CourtLocation.objects.create(
            **location_for_court_data
        )

        assert location.longitude == location_for_court_data['longitude']
        assert location.latitude == location_for_court_data['latitude']
        assert location.court_name == location_for_court_data['court_name']
        assert location.country == country_thailand
        assert location.city == city_in_thailand

        location_name: str = (
            f'{country_thailand.name}, {city_in_thailand.name}'
        )
        assert location.location_name == location_name
        assert CourtLocation.objects.count() == count_before + 1

    def test_create_tag(self, tag_data: Dict[str, Any]) -> None:
        count_before: int = Tag.objects.count()

        tag: Tag = Tag.objects.create(**tag_data)

        assert tag.name == tag_data['name']
        assert Tag.objects.count() == count_before + 1


@pytest.mark.django_db
class TestCourtModel:
    def test_create_court_without_tags_contacts(
        self,
        court_data: Dict[str, Any],
        location_for_court_thailand: CourtLocation,
    ) -> None:
        count_before: int = Court.objects.count()

        court_data.update({'location': location_for_court_thailand})
        court: Court = Court.objects.create(**court_data)

        assert court.price_description == court_data['price_description']
        assert court.description == court_data['description']
        assert court.working_hours == court_data['working_hours']
        assert Court.objects.count() == count_before + 1

    def test_create_court_without_location(
        self, court_data: Dict[str, Any]
    ) -> None:
        count_before: int = Court.objects.count()

        with transaction.atomic():
            with pytest.raises(IntegrityError):
                Court.objects.create(**court_data)

        assert Court.objects.count() == count_before

    def test_create_court_with_tags(
        self,
        court_data: Dict[str, Any],
        tag_obj: Tag,
        location_for_court_thailand: CourtLocation,
    ) -> None:
        count_before: int = Court.objects.count()

        court_data.update({'location': location_for_court_thailand})
        court: Court = Court.objects.create(**court_data)

        assert court.tag_list.count() == 0
        court.tag_list.add(tag_obj)
        assert court.tag_list.count() == 1

        tags = court.tag_list.all()
        for tag in tags:
            assert tag == tag_obj

        assert Court.objects.count() == count_before + 1

    def test_create_contact(
        self, contact_data: Dict[str, Any], court_thailand: Court
    ) -> None:
        count_before: int = Contact.objects.count()

        contact_data.update({'court': court_thailand})
        contact: Contact = Contact.objects.create(**contact_data)
        contact_rel_court: Contact | None = court_thailand.contacts.first()

        assert contact.contact_type == contact_data['contact_type']
        assert contact.contact == contact_data['contact']
        assert contact.court == court_thailand
        assert contact_rel_court == contact
        assert Contact.objects.count() == count_before + 1
