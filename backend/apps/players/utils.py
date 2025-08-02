from typing import Dict, List

from django.db import transaction
from django.db.models import QuerySet

from apps.players.models import Payment
from apps.players.serializers import PaymentSerializer


def check_payments_data(payments_data: List[Dict]) -> bool:
    """Check if payments data is correct."""
    return sum(
        1 for p in payments_data if p.get('is_preferred', False)
    ) == 1


def make_transaction(
    payments_data: List[Dict],
    queryset:QuerySet[Payment]
) -> List | None:
    """Update player payments or return error."""
    with transaction.atomic():
        updated_payments = []
        errors = []
        for payment_data in payments_data:
            try:
                payment = queryset.filter(
                    payment_type=payment_data['payment_type']
                )
                serializer = PaymentSerializer(payment, data=payment_data)
                if serializer.is_valid():
                    serializer.save()
                    updated_payments.append(serializer.data)
                else:
                    errors.append({
                        'payment_type': payment_data.get('payment_type'),
                        'errors': serializer.errors
                    })
            except Payment.DoesNotExist:
                errors.append({
                    'payment_type': payment_data.get('payment_type'),
                    'errors': 'Payment not found.'
                })
        return errors if len(errors) > 0 else None
