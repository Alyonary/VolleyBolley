from rest_framework import serializers

from apps.core.models import Contact, Tag


class TagSerializer(serializers.ModelSerializer):
    """Сериализатор всех полей модели Tag."""

    class Meta:
        exclude = ('id',)
        model = Tag


class ContactSerializer(serializers.ModelSerializer):
    """Сериализатор всех полей модели Contact."""

    class Meta:
        exclude = ('id', 'court')
        model = Contact
