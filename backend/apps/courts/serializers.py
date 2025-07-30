from rest_framework import serializers

from apps.core.serializers import ContactSerializer

from .models import Court, CourtLocation


class LocationSerializer(serializers.ModelSerializer):
    '''Location serializer for all fileds exclude id.'''

    class Meta:
        exclude = ('id',)
        model = CourtLocation


class CourtSerializer(serializers.ModelSerializer):
    '''Court model serializer.'''

    court_id = serializers.IntegerField(source='pk', read_only=True)

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
