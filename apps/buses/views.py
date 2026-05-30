from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated
from .models import Bus
from .serializers import BusSerializer


class BusViewSet(viewsets.ModelViewSet):
    queryset           = Bus.objects.all()
    serializer_class   = BusSerializer
    permission_classes = [IsAuthenticated]
    search_fields      = ['plate_number', 'color']
    ordering_fields    = ['plate_number', 'capacity']
    ordering           = ['plate_number']
