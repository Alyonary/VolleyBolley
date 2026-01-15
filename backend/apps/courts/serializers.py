from rest_framework import serializers

from apps.core.serializers import ContactSerializer
from apps.courts.models import Court, CourtLocation


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

    contact_list = ContactSerializer(many=True, source='contacts')
    photo_url = serializers.ImageField(use_url=True, required=False)

    location = LocationSerializer()

    class Meta:
        model = Court
        fields = (
            'court_id',
            'price_description',
            'description',
            'contact_list',
            'photo_url',
            'tags',
            'location',
        )
        read_only_fields = (
            'court_id',
            'price_description',
            'description',
            'contact_list',
            'photo_url',
            'tags',
            'location',
        )
