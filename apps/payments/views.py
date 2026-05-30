from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated
from .models import Payment, PaymentType
from .serializers import PaymentSerializer, PaymentTypeSerializer

class PaymentTypeViewSet(viewsets.ModelViewSet):
    queryset = PaymentType.objects.all()
    serializer_class = PaymentTypeSerializer
    permission_classes = [IsAuthenticated]

class PaymentViewSet(viewsets.ModelViewSet):
    queryset = (Payment.objects
                .select_related('trip_reservation__student__user',
                                'trip_reservation__trip__place',
                                'payment_type')
                .all())
    serializer_class   = PaymentSerializer
    permission_classes = [IsAuthenticated]
    filterset_fields   = ['status', 'payment_type']
    search_fields      = ['trip_reservation__student__user__user_name']
    ordering           = ['-created_at']
