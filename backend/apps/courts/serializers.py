from rest_framework import serializers

from apps.core.serializers import ContactSerializer, TagSerializer

from .models import Court, Location


class LocationSerializer(serializers.ModelSerializer):
    """Сериализатор всех полей модели Location."""

    class Meta:
        exclude = ('id',)
        model = Location


class CourtSerializer(serializers.ModelSerializer):
    tag_list = TagSerializer(many=True, read_only=True)

    contacts_list = ContactSerializer(many=True, read_only=True)

    location = LocationSerializer(read_only=True)

    class Meta:
        model = Court
        fields = (
            'id',
            'price_description',
            'description',
            'contacts_list',
            'photo_url',
            'tag_list',
            'location'
        )
