from rest_framework import serializers
from .models import Place, Route, Schedule

class PlaceSerializer(serializers.ModelSerializer):
    class Meta:
        model = Place
        fields = '__all__'

class ScheduleSerializer(serializers.ModelSerializer):
    class Meta:
        model  = Schedule
        fields = '__all__'

class RouteSerializer(serializers.ModelSerializer):
    schedules = ScheduleSerializer(many=True, read_only=True)
    class Meta:
        model  = Route
        fields = ['id', 'start_point', 'end_point', 'schedules']
