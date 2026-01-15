from rest_framework import serializers

from apps.core.models import Contact, CurrencyType, Tag


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


class CurrencySerializer(serializers.ModelSerializer):
    """Serializer for the CurrencyType model."""

    currency_id = serializers.IntegerField(source='id', read_only=True)
    country = serializers.SerializerMethodField()

    class Meta:
        model = CurrencyType
        fields = ('currency_id', 'currency_type', 'currency_name', 'country')
        read_only_fields = [
            'currency_id',
            'currency_type',
            'currency_name',
            'country',
        ]

    def get_country(self, obj):
        return {'country_id': obj.country.id if obj.country else None}


class CurrencyListSerializer(serializers.Serializer):
    """Serializer for list of CurrencyType objects."""

    currencies = CurrencySerializer(many=True)
