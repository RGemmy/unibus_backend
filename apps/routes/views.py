from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated
from .models import Place, Route, Schedule
from .serializers import PlaceSerializer, RouteSerializer, ScheduleSerializer

class PlaceViewSet(viewsets.ModelViewSet):
    queryset = Place.objects.all()
    serializer_class = PlaceSerializer
    permission_classes = [IsAuthenticated]
    search_fields = ['place_name']

class RouteViewSet(viewsets.ModelViewSet):
    queryset = Route.objects.prefetch_related('schedules').all()
    serializer_class = RouteSerializer
    permission_classes = [IsAuthenticated]
    search_fields = ['start_point', 'end_point']

class ScheduleViewSet(viewsets.ModelViewSet):
    queryset = Schedule.objects.select_related('route').all()
    serializer_class = ScheduleSerializer
    permission_classes = [IsAuthenticated]
    filterset_fields = ['route']
