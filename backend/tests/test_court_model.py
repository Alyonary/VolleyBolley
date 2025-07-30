from http import HTTPStatus

import pytest
from django.db import transaction
from django.db.utils import IntegrityError

from apps.core.models import Contact, Tag
from apps.courts.models import Court, CourtLocation


@pytest.mark.django_db
class TestLocationTagModel:

    def test_create_location(self, location_for_court_data):
        location = CourtLocation.objects.create(**location_for_court_data)

        assert location.longitude == location_for_court_data['longitude']
        assert location.latitude == location_for_court_data['latitude']
        assert location.court_name == location_for_court_data['court_name']
        assert location.location_name == location_for_court_data[
            'location_name'
        ]
        assert CourtLocation.objects.all().count() == 1

    def test_create_tag(self, tag_data):
        tag = Tag.objects.create(**tag_data)

        assert tag.name == tag_data['name']
        assert Tag.objects.all().count() == 1


@pytest.mark.django_db
class TestCourtModel:

    def test_create_court_without_tags_contacts(self, court_data):
        court = Court.objects.create(**court_data)

        assert court.location == court_data['location']
        assert court.price_description == court_data['price_description']
        assert court.description == court_data['description']
        assert court.working_hours == court_data['working_hours']
        assert Court.objects.all().count() == 1

    def test_create_court_without_location(self, court_data):
        court_data.pop('location')
        with transaction.atomic():
            with pytest.raises(IntegrityError):
                Court.objects.create(**court_data)
        assert Court.objects.all().count() == 0

    def test_create_court_with_tags(self, court_data, tag_obj):
        court = Court.objects.create(**court_data)

        court.tag_list.add(tag_obj)
        assert court.tag_list.count() == 1

        tags = court.tag_list.all()
        for tag in tags:
            assert tag == tag_obj

    def test_create_contact(self, contact_data, court_obj):
        contact = Contact.objects.create(**contact_data)
        contact_rel_court = court_obj.contacts.first()
        assert contact.contact_type == contact_data['contact_type']
        assert contact.contact == contact_data['contact']
        assert contact.court == court_obj
        assert contact_rel_court == contact


@pytest.mark.django_db(transaction=True)
class TestCourtApiModel:

    def test_api_url(self, api_client, court_list_url):
        response = api_client.get(court_list_url)
        assert response.status_code == HTTPStatus.OK

    def test_response_structure(
            self,
            api_client,
            court_list_url,
            court_api_response_data,
            court_obj_with_tag,
            contact_object
            ):
        response = api_client.get(court_list_url)
        answer = response.data[0]
        assert answer.keys() == court_api_response_data.keys()
        assert answer['contacts_list'] == court_api_response_data[
            'contacts_list']
        assert answer['tag_list'] == court_api_response_data['tag_list']
        assert answer['location'].keys() == court_api_response_data[
            'location'].keys()
        assert answer['court_id'] == court_obj_with_tag.id

    def test_filter_response(
            self,
            api_client,
            court_list_url,
            location_for_court_data,
            court_data,
            court_obj
            ):

        location_for_court_data['court_name'] = 'Another court'
        another_location = CourtLocation.objects.create(
            **location_for_court_data)
        court_data['location'] = another_location
        Court.objects.create(**court_data)
        court_list_url += '?search=Another'
        response = api_client.get(court_list_url)
        assert response.data[0]['location']['court_name'] == 'Another court'
        assert len(response.data) == 1
        assert Court.objects.all().count() == 2
