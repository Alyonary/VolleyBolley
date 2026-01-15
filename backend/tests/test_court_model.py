import pytest
from django.db import transaction
from django.db.utils import IntegrityError
from rest_framework import status

from apps.core.models import Contact, Tag
from apps.courts.models import Court, CourtLocation


@pytest.mark.django_db
class TestLocationTagModel:
    def test_create_location(
        self, location_for_court_data, country_thailand, city_in_thailand
    ):
        location_for_court_data.update(
            {'country': country_thailand, 'city': city_in_thailand}
        )
        location = CourtLocation.objects.create(**location_for_court_data)

        assert location.longitude == location_for_court_data['longitude']
        assert location.latitude == location_for_court_data['latitude']
        assert location.court_name == location_for_court_data['court_name']
        assert location.country == country_thailand
        assert location.city == city_in_thailand
        location_name = f'{country_thailand.name}, {city_in_thailand.name}'
        assert location.location_name == location_name

        assert CourtLocation.objects.all().count() == 1

    def test_create_tag(self, tag_data):
        tag = Tag.objects.create(**tag_data)

        assert tag.name == tag_data['name']
        assert Tag.objects.all().count() == 1


@pytest.mark.django_db
class TestCourtModel:
    def test_create_court_without_tags_contacts(
        self, court_data, location_for_court_thailand
    ):
        court_data.update({'location': location_for_court_thailand})
        court = Court.objects.create(**court_data)

        assert court.price_description == court_data['price_description']
        assert court.description == court_data['description']
        assert court.working_hours == court_data['working_hours']
        assert Court.objects.all().count() == 1

    def test_create_court_without_location(self, court_data):
        with transaction.atomic():
            with pytest.raises(IntegrityError):
                Court.objects.create(**court_data)
        assert Court.objects.all().count() == 0

    def test_create_court_with_tags(
        self, court_data, tag_obj, location_for_court_thailand
    ):
        court_data.update({'location': location_for_court_thailand})
        court = Court.objects.create(**court_data)

        court.tag_list.add(tag_obj)
        assert court.tag_list.count() == 1

        tags = court.tag_list.all()
        for tag in tags:
            assert tag == tag_obj

    def test_create_contact(self, contact_data, court_thailand):
        contact = Contact.objects.create(**contact_data)
        contact_rel_court = court_thailand.contacts.first()
        assert contact.contact_type == contact_data['contact_type']
        assert contact.contact == contact_data['contact']
        assert contact.court == court_thailand
        assert contact_rel_court == contact


@pytest.mark.django_db(transaction=True)
class TestCourtApiModel:
    @pytest.mark.parametrize(
        'client_fixture_name,expected_status',
        [
            ('api_client', status.HTTP_401_UNAUTHORIZED),
            (
                'auth_api_client_with_not_registered_player',
                status.HTTP_403_FORBIDDEN,
            ),
            ('auth_api_client_registered_player', status.HTTP_200_OK),
        ],
    )
    def test_api_url(
        self, request, client_fixture_name, expected_status, court_list_url
    ):
        client = request.getfixturevalue(client_fixture_name)
        response = client.get(court_list_url)
        assert response.status_code == expected_status

    def test_response_structure(
        self,
        auth_api_client_registered_player,
        court_list_url,
        court_api_response_data,
        court_obj_with_tag,
        contact_object,
    ):
        response = auth_api_client_registered_player.get(court_list_url)
        answer = response.data[0]
        assert answer.keys() == court_api_response_data.keys()
        assert (
            answer['contacts_list'] == court_api_response_data['contacts_list']
        )
        assert answer['tags'] == court_api_response_data['tags']
        assert (
            answer['location'].keys()
            == court_api_response_data['location'].keys()
        )
        assert answer['court_id'] == court_obj_with_tag.id

    def test_filter_response(
        self,
        auth_api_client_registered_player,
        court_list_url,
        court_cyprus,
        court_thailand,
    ):
        court_list_url += '?search=Tha'
        response = auth_api_client_registered_player.get(court_list_url)
        assert Court.objects.all().count() == 2
        assert len(response.data) == 1
        assert (
            response.data[0]['location']['court_name']
            != court_cyprus.location.court_name
        )
        assert (
            response.data[0]['location']['court_name']
            == court_thailand.location.court_name
        )

    def test_filter_qs_for_player(
        self,
        court_list_url,
        court_cyprus,
        court_thailand,
        auth_api_client_registered_player,
    ):
        response = auth_api_client_registered_player.get(court_list_url)
        assert Court.objects.count() == 2
        assert len(response.data) == 1
        assert response.data[0]['court_id'] == court_thailand.id
