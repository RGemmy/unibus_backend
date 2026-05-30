from rest_framework import serializers
from .models import TripReservation


class TripReservationSerializer(serializers.ModelSerializer):
    student_name  = serializers.CharField(source='student.user.user_name', read_only=True)
    trip_place    = serializers.CharField(source='trip.place.place_name',  read_only=True)
    trip_date     = serializers.DateField(source='trip.trip_date',         read_only=True)
    schedule_time = serializers.TimeField(source='trip.schedule.schedule_time', read_only=True)

    class Meta:
        model  = TripReservation
        fields = [
            'id', 'student', 'student_name',
            'trip', 'trip_place', 'trip_date', 'schedule_time',
            'trip_reservation_date', 'status',
            'gps_sharing', 'gps_latitude', 'gps_longitude', 'gps_updated_at',
        ]
        read_only_fields = ['trip_reservation_date', 'gps_updated_at']

    def validate(self, data):
        trip = data.get('trip')
        if trip and trip.available_seats <= 0:
            raise serializers.ValidationError('لا توجد مقاعد متاحة في هذه الرحلة')
        return data


class GPSUpdateSerializer(serializers.Serializer):
    """Serializer مخصص لتحديث الـ GPS فقط."""
    latitude  = serializers.DecimalField(max_digits=9, decimal_places=6)
    longitude = serializers.DecimalField(max_digits=9, decimal_places=6)

    def validate_latitude(self, value):
        if not (-90 <= float(value) <= 90):
            raise serializers.ValidationError('خط العرض يجب أن يكون بين -90 و 90')
        return value

    def validate_longitude(self, value):
        if not (-180 <= float(value) <= 180):
            raise serializers.ValidationError('خط الطول يجب أن يكون بين -180 و 180')
        return value
