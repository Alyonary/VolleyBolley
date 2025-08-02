import pytest
from apps.locations.models import City, Country


@pytest.fixture
def countries_cities():
    '''Create test cities and countries data.'''
    thailand = Country.objects.create(name='Thailand')
    cyprus = Country.objects.create(name='Cyprus')
    
    City.objects.create(name='Bangkok', country=thailand)
    City.objects.create(name='Pattaya', country=thailand)
    City.objects.create(name='Limassol', country=cyprus)
    City.objects.create(name='Nicosia', country=cyprus)
    
    return {'thailand': thailand, 'cyprus': cyprus}

@pytest.fixture
def countries_cities_data():
    return {
        'countries': [
            {
                'name': 'Thailand'
            },
            {
                'name': 'Cyprus'
            }
        ],
        'cities': [
            {
                'name': 'Bangkok',
                'country': 'Thailand'
            },
            {
                'name': 'Paphos',
                'country': 'Cyprus'
            }
        ]
    }