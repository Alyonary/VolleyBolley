from django.core.exceptions import ValidationError
from django.core.validators import validate_email
from rest_framework import serializers

from apps.core.constants import DOMAIN_REGEX, ContactTypes
from apps.core.models import Contact, CurrencyType, GameLevel, Tag
from apps.courts.models import Court
from apps.locations.models import Country


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


class CurrencyCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating CurrencyType."""

    currency_type = serializers.ChoiceField(
        choices=CurrencyType.CurrencyTypeChoices.choices
    )
    currency_name = serializers.ChoiceField(
        choices=CurrencyType.CurrencyNameChoices.choices
    )
    country = serializers.CharField()

    class Meta:
        model = CurrencyType
        fields = ['currency_type', 'currency_name', 'country']

    def validate_country(self, value):
        value = value.strip()
        if not value:
            raise serializers.ValidationError('Country is required.')
        try:
            return Country.objects.get(name=value)
        except Country.DoesNotExist as e:
            raise serializers.ValidationError(
                f'Country "{value}" does not exist.'
            ) from e


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


class GameLevelSerializer(serializers.ModelSerializer):
    """Serializer for GameLevel model."""

    name = serializers.ChoiceField(choices=GameLevel.GameLevelChoices.choices)

    class Meta:
        model = GameLevel
        fields = [
            'name',
        ]


class ContactCreateSerializer(serializers.ModelSerializer):
    """Serializer for Contact model."""

    contact_type = serializers.ChoiceField(choices=ContactTypes.choices)
    court = serializers.PrimaryKeyRelatedField(
        queryset=Court.objects.all(), required=True, write_only=True
    )

    class Meta:
        model = Contact
        fields = ['contact_type', 'contact', 'court']

    def validate(self, attrs):
        contact_type = attrs.get('contact_type')
        contact = attrs.get('contact')
        if contact_type and not contact:
            raise serializers.ValidationError(
                f'Contact value is required for contact type "{contact_type}".'
            )
        if contact_type == ContactTypes.PHONE and not contact.isdigit():
            raise serializers.ValidationError(
                'Phone contact must contain only digits.'
            )
        if contact_type == ContactTypes.EMAIL:
            try:
                validate_email(contact)
            except ValidationError as err:
                raise serializers.ValidationError(
                    'Invalid email address format.'
                ) from err
        elif contact_type == ContactTypes.WEBSITE:
            if not DOMAIN_REGEX.match(contact):
                raise serializers.ValidationError(
                    'Invalid domain name format.'
                )
        return attrs

    def create(self, validated_data):
        contact, _ = Contact.objects.get_or_create(**validated_data)
        return contact
