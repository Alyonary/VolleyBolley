from rest_framework import serializers

from .models import Contact, Court, Location, Tag


class TagSerializer(serializers.ModelSerializer):
    """Сериализатор всех полей модели Tag."""

    class Meta:
        exclude = ('id',)
        model = Tag


class LocationSerializer(serializers.ModelSerializer):
    """Сериализатор всех полей модели Location."""

    class Meta:
        exclude = ('id',)
        model = Location


class ContactSerializer(serializers.ModelSerializer):
    """Сериализатор всех полей модели Contact."""

    class Meta:
        exclude = ('id',)
        model = Contact


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
