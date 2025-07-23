from rest_framework import serializers

from apps.locations.models import City, Country


class CitySerializer(serializers.ModelSerializer):
    '''Serializer for City model.'''
    
    city_id = serializers.IntegerField(source='id', read_only=True)
    city_name = serializers.CharField(source='name', read_only=True)

    class Meta:
        model = City
        fields = ['city_id', 'city_name']


class CountrySerializer(serializers.ModelSerializer):
    '''Serializer for Country model with nested cities.'''
    
    country_id = serializers.IntegerField(source='id', read_only=True)
    country_name = serializers.CharField(source='name', read_only=True)
    cities = CitySerializer(many=True, read_only=True)

    class Meta:
        model = Country
        fields = ['country_id', 'country_name', 'cities']
