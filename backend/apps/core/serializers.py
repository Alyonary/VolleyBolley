from django.utils.translation import gettext_lazy as _
from rest_framework import serializers

from apps.core.models import Contact, Payment, Tag


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


class PaymentSerializer(serializers.ModelSerializer):

    owner = serializers.HiddenField(
        write_only=True,
        default=serializers.CurrentUserDefault()
    )

    class Meta:
        model = Payment
        exclude = ('id',)
        validators = [
            serializers.UniqueTogetherValidator(
                queryset=Payment.objects.all(),
                fields=('owner', 'payment_type'),
                message=_('This payment type already exists.'),
            )
        ]
