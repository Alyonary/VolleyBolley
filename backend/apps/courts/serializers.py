from rest_framework import serializers

from apps.core.serializers import ContactSerializer
from apps.courts.models import Court, CourtLocation
from apps.locations.models import City, Country


class LocationSerializer(serializers.ModelSerializer):
    """Location serializer for all fields exclude id."""

    location_name = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = CourtLocation
        fields = ('latitude', 'longitude', 'court_name', 'location_name')
        read_only_fields = (
            'latitude',
            'longitude',
            'court_name',
            'location_name',
        )

    def get_location_name(self, obj):
        return obj.location_name


class CourtSerializer(serializers.ModelSerializer):
    """Court model serializer."""

    court_id = serializers.IntegerField(source='pk')

    tags = serializers.StringRelatedField(source='tag_list', many=True)

    contacts_list = ContactSerializer(many=True, source='contacts')
    photo_url = serializers.ImageField(use_url=True, required=False)

    location = LocationSerializer()

    class Meta:
        model = Court
        fields = (
            'court_id',
            'price_description',
            'description',
            'contacts_list',
            'photo_url',
            'tags',
            'location',
        )
        read_only_fields = (
            'court_id',
            'price_description',
            'description',
            'contacts_list',
            'photo_url',
            'tags',
            'location',
        )


class LocationsCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating CourtLocation with country and city names."""

    city = serializers.CharField()
    country = serializers.CharField()

    class Meta:
        model = CourtLocation
        fields = [
            'longitude',
            'latitude',
            'court_name',
            'country',
            'city',
        ]

    def validate_country(self, value):
        try:
            Country.objects.get(name=value)
        except Country.DoesNotExist as e:
            raise serializers.ValidationError(
                f'Country "{value}" does not exist.'
            ) from e
        return value

    def validate_city(self, value):
        try:
            City.objects.get(name=value)
        except City.DoesNotExist as e:
            raise serializers.ValidationError(
                f'City "{value}" does not exist.'
            ) from e
        return value

    def create(self, validated_data):
        country_obj = Country.objects.get(name=validated_data.pop('country'))
        city_obj = City.objects.get(name=validated_data.pop('city'))
        location_obj, _ = CourtLocation.objects.get_or_create(
            country=country_obj, city=city_obj, **validated_data
        )
        return location_obj


class CourtCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating Court."""

    location = LocationsCreateSerializer()

    class Meta:
        model = Court
        fields = [
            'location',
            'price_description',
            'description',
            'photo_url',
            'working_hours',
        ]

    def create(self, validated_data):
        location_data = validated_data.pop('location')
        location_serializer = LocationsCreateSerializer(data=location_data)
        location_serializer.is_valid(raise_exception=True)
        location = location_serializer.save()
        return Court.objects.create(location=location, **validated_data)
