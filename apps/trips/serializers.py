from rest_framework import serializers
from .models import Trip
from apps.buses.serializers import BusSerializer
from apps.routes.serializers import PlaceSerializer, ScheduleSerializer


class TripSerializer(serializers.ModelSerializer):
    place_name    = serializers.CharField(source='place.place_name', read_only=True)
    bus_plate     = serializers.CharField(source='bus.plate_number', read_only=True)
    bus_capacity  = serializers.IntegerField(source='bus.capacity', read_only=True)
    schedule_time = serializers.TimeField(source='schedule.schedule_time', read_only=True)
    reserved_seats   = serializers.IntegerField(read_only=True)
    available_seats  = serializers.IntegerField(read_only=True)

    class Meta:
        model  = Trip
        fields = [
            'id', 'place', 'place_name', 'bus', 'bus_plate', 'bus_capacity',
            'schedule', 'schedule_time', 'trip_date', 'status', 'end_time',
            'reserved_seats', 'available_seats', 'created_at',
        ]
        read_only_fields = ['created_at']
