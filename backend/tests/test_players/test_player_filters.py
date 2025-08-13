import pytest
from django.contrib.auth import get_user_model
from rest_framework.test import APIRequestFactory

from apps.locations.models import City, Country
from apps.players.filters import PlayersFilter
from apps.players.models import Player

User = get_user_model()


@pytest.fixture
def setup_test_data():
    '''Creates test data for filters.'''
    thailand = Country.objects.create(name='Thailand')
    cyprus = Country.objects.create(name='Cyprus')
    
    bangkok = City.objects.create(
        country=thailand, name='Bangkok'
    )
    pattaya = City.objects.create(
        country=thailand, name='Pattaya'
    )
    City.objects.create(
        country=thailand, name='Chiang Mai'
    )
    limassol = City.objects.create(
        country=cyprus, name='Limassol'
    )
    nicosia = City.objects.create(
        country=cyprus, name='Nicosia'
    )
    larnaca = City.objects.create(
        country=cyprus, name='Larnaca'
    )
    john_bangkok_user = User.objects.create_user(
        username='john_bangkok',
        first_name='John',
        last_name='Smith',
        email='john.bangkok@example.com',
    )
    john_pattaya_user = User.objects.create_user(
        username='john_pattaya',
        first_name='John',
        last_name='Doe',
        email='john.pattaya@example.com',
    )
    jane_bangkok_user = User.objects.create_user(
        username='jane_bangkok',
        first_name='Jane',
        last_name='Wilson',
        email='jane.bangkok@example.com',
    )
    requesting_user_bangkok = User.objects.create_user(
        username='requesting_user_bangkok',
        first_name='Mike',
        last_name='Johnson',
        email='mike.bangkok@example.com',
    )
    requesting_user_pattaya = User.objects.create_user(
        username='requesting_user_pattaya',
        first_name='Alex',
        last_name='Brown',
        email='alex.pattaya@example.com',
    )
    john_limassol_user = User.objects.create_user(
        username='john_limassol',
        first_name='John',
        last_name='Green',
        email='john.limassol@example.com',
    )
    john_nicosia_user = User.objects.create_user(
        username='john_nicosia',
        first_name='John',
        last_name='White',
        email='john.nicosia@example.com',
    )
    jane_larnaca_user = User.objects.create_user(
        username='jane_larnaca',
        first_name='Jane',
        last_name='Black',
        email='jane.larnaca@example.com',
    )
    requesting_user_limassol = User.objects.create_user(
        username='requesting_user_limassol',
        first_name='Maria',
        last_name='Miller',
        email='maria.limassol@example.com',
    )
    john_bangkok = Player.objects.create(
        user=john_bangkok_user,
        gender='MALE',
        level='LIGHT',
        country=thailand,
        city=bangkok
    )
    john_pattaya = Player.objects.create(
        user=john_pattaya_user,
        gender='MALE',
        level='PRO',
        country=thailand,
        city=pattaya
    )
    jane_bangkok = Player.objects.create(
        user=jane_bangkok_user,
        gender='FEMALE',
        level='LIGHT',
        country=thailand,
        city=bangkok
    )
    requesting_player_bangkok = Player.objects.create(
        user=requesting_user_bangkok,
        gender='MALE',
        level='PRO',
        country=thailand,
        city=bangkok
    )
    requesting_player_pattaya = Player.objects.create(
        user=requesting_user_pattaya,
        gender='MALE',
        level='LIGHT',
        country=thailand,
        city=pattaya
    )
    john_limassol = Player.objects.create(
        user=john_limassol_user,
        gender='MALE',
        level='LIGHT',
        country=cyprus,
        city=limassol
    )
    john_nicosia = Player.objects.create(
        user=john_nicosia_user,
        gender='MALE',
        level='PRO',
        country=cyprus,
        city=nicosia
    )
    jane_larnaca = Player.objects.create(
        user=jane_larnaca_user,
        gender='FEMALE',
        level='LIGHT',
        country=cyprus,
        city=larnaca
    )
    requesting_player_limassol = Player.objects.create(
        user=requesting_user_limassol,
        gender='FEMALE',
        level='PRO',
        country=cyprus,
        city=limassol
    )
    return {
        'countries': Country.objects.all(),
        'thailand_cities': City.objects.filter(country=thailand),
        'cyprus_cities': City.objects.filter(country=cyprus),
        'cyprus_players': [john_limassol, john_nicosia, jane_larnaca],
        'thailand_players': [john_bangkok, john_pattaya, jane_bangkok],
        'requesting_player_bangkok': requesting_player_bangkok,
        'requesting_player_pattaya': requesting_player_pattaya,
        'requesting_player_limassol': requesting_player_limassol,
    }


@pytest.mark.django_db
class TestPlayersFilter:
    '''Tests for player filter with location sorting.'''

    def test_thailand_user_sees_only_same_city_players(self, setup_test_data):
        '''Test Thailand users only see players from their city.'''
        factory = APIRequestFactory()
        request = factory.get('/players/?search=John')
        request.user = setup_test_data['requesting_player_bangkok'].user

        data = {'search': 'John'}
        filter_instance = PlayersFilter(data, queryset=Player.objects.all())
        filter_instance.request = request

        filtered_players = filter_instance.qs

        assert filtered_players.count() == 1
        player = filtered_players.first()
        assert player.user.first_name == 'John'
        assert player.city.name == 'Bangkok'
        assert player.user.username == 'john_bangkok'

    def test_thailand_user_different_city_no_cross_city_results(
        self, setup_test_data
    ):
        '''Test Thailand user from Pattaya doesn't see Bangkok players.'''
        factory = APIRequestFactory()
        request = factory.get('/players/?search=John')
        request.user = setup_test_data['requesting_player_pattaya'].user

        data = {'search': 'John'}
        filter_instance = PlayersFilter(data, queryset=Player.objects.all())
        filter_instance.request = request

        filtered_players = filter_instance.qs

        assert filtered_players.count() == 1
        player = filtered_players.first()
        assert player.user.first_name == 'John'
        assert player.city.name == 'Pattaya'
        assert player.user.username == 'john_pattaya'

    def test_cyprus_user_sees_all_cyprus_cities(self, setup_test_data):
        '''Test Cyprus users see players from all Cyprus cities.'''
        factory = APIRequestFactory()
        request = factory.get('/players/?search=John')
        request.user = setup_test_data['requesting_player_limassol'].user

        data = {'search': 'John'}
        filter_instance = PlayersFilter(data, queryset=Player.objects.all())
        filter_instance.request = request

        filtered_players = list(filter_instance.qs)

        assert len(filtered_players) == 2

        cities = [p.city.name for p in filtered_players]
        countries = [p.country.name for p in filtered_players]

        assert 'Limassol' in cities
        assert 'Nicosia' in cities
        assert all(country == 'Cyprus' for country in countries)

    def test_cyprus_user_no_thailand_players_in_results(self, setup_test_data):
        '''Test Cyprus users don't see Thailand players.'''
        factory = APIRequestFactory()
        request = factory.get('/players/?search=John')
        request.user = setup_test_data['requesting_player_limassol'].user

        data = {'search': 'John'}
        filter_instance = PlayersFilter(data, queryset=Player.objects.all())
        filter_instance.request = request

        filtered_players = list(filter_instance.qs)

        thailand_players = [
            p for p in filtered_players if p.country.name == 'Thailand'
        ]
        cyprus_players = [
            p for p in filtered_players if p.country.name == 'Cyprus'
        ]

        assert len(thailand_players) == 0
        assert len(cyprus_players) == 2

    def test_cyprus_user_multiple_cities_same_name(self, setup_test_data):
        '''Test Cyprus user sees players with same name from other cities.'''
        factory = APIRequestFactory()
        request = factory.get('/players/?search=Jane')
        request.user = setup_test_data['requesting_player_limassol'].user

        data = {'search': 'Jane'}
        filter_instance = PlayersFilter(data, queryset=Player.objects.all())
        filter_instance.request = request

        filtered_players = list(filter_instance.qs)

        cities = [p.city.name for p in filtered_players]
        countries = [p.country.name for p in filtered_players]

        assert len(filtered_players) == 1
        assert 'Larnaca' in cities
        assert all(country == 'Cyprus' for country in countries)

    def test_thailand_city_isolation(self, setup_test_data):
        '''Test that Thailand cities are properly isolated.'''
        factory = APIRequestFactory()

        request_bangkok = factory.get('/players/?search=Jane')
        request_bangkok.user = setup_test_data[
            'requesting_player_bangkok'
        ].user

        filter_bangkok = PlayersFilter(
            {'search': 'Jane'}, queryset=Player.objects.all()
        )
        filter_bangkok.request = request_bangkok
        bangkok_results = list(filter_bangkok.qs)

        request_pattaya = factory.get('/players/?search=Jane')
        request_pattaya.user = setup_test_data[
            'requesting_player_pattaya'
        ].user

        filter_pattaya = PlayersFilter(
            {'search': 'Jane'}, queryset=Player.objects.all()
        )
        filter_pattaya.request = request_pattaya
        pattaya_results = list(filter_pattaya.qs)

        assert len(bangkok_results) == 1
        assert bangkok_results[0].city.name == 'Bangkok'
        assert bangkok_results[0].user.first_name == 'Jane'

        assert len(pattaya_results) == 0

    def test_cyprus_country_wide_search(self, setup_test_data):
        '''Test Cyprus search works country-wide, not city-specific.'''
        factory = APIRequestFactory()
        request = factory.get('/players/?search=John')
        request.user = setup_test_data['requesting_player_limassol'].user

        data = {'search': 'John'}
        filter_instance = PlayersFilter(data, queryset=Player.objects.all())
        filter_instance.request = request

        filtered_players = list(filter_instance.qs)

        cities = set(p.city.name for p in filtered_players)
        countries = set(p.country.name for p in filtered_players)

        assert len(cities) == 2
        assert 'Limassol' in cities
        assert 'Nicosia' in cities
        assert countries == {'Cyprus'}

    @pytest.mark.parametrize(
        'requesting_city,search_term,expected_cities,expected_count',
        [
            ('Bangkok', 'John', ['Bangkok'], 1),
            ('Pattaya', 'John', ['Pattaya'], 1),
            ('Bangkok', 'Jane', ['Bangkok'], 1),
            ('Pattaya', 'Jane', [], 0),
            ('Limassol', 'John', ['Limassol', 'Nicosia'], 2),
            ('Limassol', 'Jane', ['Larnaca'], 1),
        ],
    )
    def test_location_filtering_parametrized(
        self,
        setup_test_data,
        requesting_city,
        search_term,
        expected_cities,
        expected_count,
    ):
        '''Parametrized test for location filtering behavior.'''
        factory = APIRequestFactory()

        if requesting_city == 'Bangkok':
            requesting_user = setup_test_data['requesting_player_bangkok'].user
        elif requesting_city == 'Pattaya':
            requesting_user = setup_test_data['requesting_player_pattaya'].user
        elif requesting_city == 'Limassol':
            requesting_user = setup_test_data[
                'requesting_player_limassol'
            ].user

        request = factory.get(f'/players/?search={search_term}')
        request.user = requesting_user

        filter_instance = PlayersFilter(
            {'search': search_term}, queryset=Player.objects.all()
        )
        filter_instance.request = request

        filtered_players = list(filter_instance.qs)
        result_cities = [p.city.name for p in filtered_players]

        assert len(filtered_players) == expected_count
        assert set(result_cities) == set(expected_cities)

    def test_relevance_sorting_within_location_constraints(
        self, setup_test_data
    ):
        '''Test relevance sorting works within location constraints.'''
        factory = APIRequestFactory()
        request = factory.get('/players/?search=J')
        request.user = setup_test_data['requesting_player_bangkok'].user

        johnny_user = User.objects.create_user(
            username='johnny_bangkok',
            first_name='Johnny',
            last_name='Test',
            email='johnny@example.com',
        )
        Player.objects.create(
            user=johnny_user,
            gender='MALE',
            level='LIGHT',
            country=setup_test_data['countries'].get(name='Thailand'),
            city=setup_test_data['thailand_cities'].get(name='Bangkok')
        )

        data = {'search': 'J'}
        filter_instance = PlayersFilter(data, queryset=Player.objects.all())
        filter_instance.request = request

        filtered_players = list(filter_instance.qs)

        bangkok_players = [
            p for p in filtered_players if p.city.name == 'Bangkok'
        ]
        assert len(bangkok_players) == len(filtered_players)

        names = [p.user.first_name for p in filtered_players]
        assert 'John' in names
        assert 'Jane' in names
        assert 'Johnny' in names

    def test_empty_search_returns_all_players(self, setup_test_data):
        '''Test that empty search returns all players.'''
        factory = APIRequestFactory()
        request = factory.get('/players/?search=')
        request.user = setup_test_data['requesting_player_bangkok'].user

        data = {'search': ''}
        filter_instance = PlayersFilter(data, queryset=Player.objects.all())
        filter_instance.request = request

        filtered_players = filter_instance.qs
        total_players = Player.objects.count()

        assert filtered_players.count() == total_players


@pytest.mark.django_db
class TestPlayersFilterAPI:
    '''Class for API filter tests.'''

    pass
