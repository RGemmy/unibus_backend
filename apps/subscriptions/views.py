from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from .models import Subscription
from .serializers import SubscriptionSerializer


class SubscriptionViewSet(viewsets.ModelViewSet):
    queryset = Subscription.objects.select_related('student__user').all()
    serializer_class   = SubscriptionSerializer
    permission_classes = [IsAuthenticated]
    filterset_fields   = ['status', 'student']
    search_fields      = ['student__user__user_name']
    ordering           = ['-start_date']

    @action(detail=True, methods=['patch'], url_path='cancel')
    def cancel(self, request, pk=None):
        sub = self.get_object()
        sub.status = 'cancelled'
        sub.save()
        return Response(self.get_serializer(sub).data)
