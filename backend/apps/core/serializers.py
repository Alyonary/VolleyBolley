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


class CurrencyTypeCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating CurrencyType."""

    currency_type = serializers.ChoiceField(
        choices=CurrencyType.CurrencyTypeChoices.choices
    )
    currency_name = serializers.ChoiceField(
        choices=CurrencyType.CurrencyNameChoices.choices
    )
    class Meta:
        model = CurrencyType
        fields = ['currency_type', 'currency_name', 'country']

    def validate_country(self, value):
        value = value.strip()
        if not value:
            raise serializers.ValidationError('Country is required.')
        try:
            Country.objects.get(name=value)
        except Country.DoesNotExist as e:
            raise serializers.ValidationError(
                f'Country "{value}" does not exist.'
            ) from e
        return value

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
