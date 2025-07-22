from rest_framework import serializers

from apps.core.serializers import ContactSerializer, TagSerializer

from .models import Court, Location


class LocationSerializer(serializers.ModelSerializer):
    '''Location serializer for all fileds exclude id.'''

    class Meta:
        exclude = ('id',)
        model = Location


class CourtSerializer(serializers.ModelSerializer):

    tag_list = serializers.StringRelatedField(many=True, read_only=True)

    contacts_list = ContactSerializer(
        many=True,
        source='contacts',
        read_only=True
    )

    location = LocationSerializer(read_only=True)

    class Meta:
        model = Court
        fields = (
            #'court_id',
            'price_description',
            'description',
            'contacts_list',
            'photo_url',
            'tag_list',
            'location'
        )

    def to_representation(self, instance):
        repr = super().to_representation(instance)
        repr['court_id'] = instance.pk
        return repr
