from rest_framework.viewsets import ModelViewSet

from .models import Payment
from .serializers import PaymentSerializer


class PaymentViewSet(ModelViewSet):
    queryset = Payment.objects.select_related('owner')
    serializer_class = PaymentSerializer
    http_method_names = ['get', 'put']

    def perform_create(self, serializer):
        serializer.save(
            owner=self.request.user)
