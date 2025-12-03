from rest_framework import serializers

from apps.core.models import Contact, Tag


class TagSerializer(serializers.ModelSerializer):
    """Serializer for all fields of the Tag model."""

    class Meta:
        exclude = ('id',)
        model = Tag


class ContactSerializer(serializers.ModelSerializer):
    """Serializer for all fields of the Contact model."""

    class Meta:
        exclude = ('id', 'court')
        model = Contact


class EmptyBodySerializer(serializers.Serializer):
    pass
