from rest_framework import serializers

from apps.core.serializers import ContactSerializer
from apps.courts.models import Court, CourtLocation


class LocationSerializer(serializers.ModelSerializer):
    """Location serializer for all fileds exclude id."""

    location_name = serializers.SerializerMethodField(read_only=True)

    class Meta:
        fields = ('latitude', 'longitude', 'court_name', 'location_name')
        model = CourtLocation

    def get_location_name(self, obj):
        return obj.location_name


class CourtSerializer(serializers.ModelSerializer):
    """Court model serializer."""

    court_id = serializers.IntegerField(source='pk')

    tag_list = serializers.StringRelatedField(many=True)

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
            'tag_list',
            'location',
        )
        read_only_fields = (
            'court_id',
            'price_description',
            'description',
            'contacts_list',
            'photo_url',
            'tag_list',
            'location',
        )
