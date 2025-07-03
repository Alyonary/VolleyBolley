from django.contrib.auth import get_user_model
from rest_framework import serializers

from apps.users.models import Location

User = get_user_model()


class LocationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Location
        fields = (
            'country',
            'city',
        )


class UserSerializer(serializers.ModelSerializer):
    location = LocationSerializer(required=False, allow_null=True)

    class Meta:
        model = User
        fields = (
            'id',
            'first_name',
            'last_name',
            'gender',
            'birth_date',
            'email',
            'password',
            'location',
        )
        extra_kwargs = {'password': {'write_only': True, 'min_length': 5}}

    def create(self, validated_data):
        location_data = validated_data.pop('location', None)
        if location_data:
            location, _ = Location.objects.get_or_create(**location_data)
            validated_data['location'] = location
        return User.objects.create_user(**validated_data)
