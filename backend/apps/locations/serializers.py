from rest_framework import serializers

from apps.locations.models import City, Country


class CitySerializer(serializers.ModelSerializer):
    """Serializer for City model."""

    city_id = serializers.IntegerField(source='id', read_only=True)
    city_name = serializers.CharField(source='name', read_only=True)

    class Meta:
        model = City
        fields = ['city_id', 'city_name']


class CountrySerializer(serializers.ModelSerializer):
    """Serializer for Country model with nested cities."""

    country_id = serializers.IntegerField(source='id', read_only=True)
    country_name = serializers.CharField(source='name', read_only=True)
    cities = CitySerializer(many=True, read_only=True)

    class Meta:
        model = Country
        fields = ['country_id', 'country_name', 'cities']


class CountryListSerializer(serializers.Serializer):
    """Serializer for countries with nested cities."""

    countries = CountrySerializer(many=True, read_only=True)


class CountryCreateSerializer(serializers.ModelSerializer):
    """
    Serializer for creating Country instances.
    Validates that the country name is provided and is a string of letters.
    """

    class Meta:
        model = Country
        fields = ['name']

    def validate_name(self, value):
        if not isinstance(value, str) or not value.isalpha():
            raise serializers.ValidationError(
                'Country name must be a string of letters.'
            )
        return value


class CityCreateSerializer(serializers.ModelSerializer):
    """
    Serializer for creating City instances.
    Validates that the city name is provided and the associated country exists.

    """

    country = serializers.CharField()

    class Meta:
        model = City
        fields = ['name', 'country']

    def validate_name(self, value):
        value = value.strip()
        if not value:
            raise serializers.ValidationError('City name is required.')
        return value

    def validate_country(self, value):
        value = value.strip()
        if not value:
            raise serializers.ValidationError('Country is required for city.')
        try:
            return Country.objects.get(name=value)
        except Country.DoesNotExist as e:
            raise serializers.ValidationError(
                f'Country "{value}" does not exist.'
            ) from e

    def validate(self, attrs):
        name = attrs.get('name')
        country = attrs.get('country')
        if name and country:
            if City.objects.filter(name=name, country=country).exists():
                raise serializers.ValidationError(
                    'City with this name and country already exists.'
                )
        return attrs
