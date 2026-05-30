from rest_framework import serializers
from .models import WaitlistEntry, CreditBalance, StudentNotification


class WaitlistEntrySerializer(serializers.ModelSerializer):
    student_name   = serializers.CharField(source='student.user.user_name', read_only=True)
    student_phone  = serializers.CharField(source='student.user.phone',     read_only=True, default='')
    trip_place     = serializers.CharField(source='trip.place.place_name',  read_only=True)
    trip_date      = serializers.DateField(source='trip.trip_date',         read_only=True)
    schedule_time  = serializers.TimeField(source='trip.schedule.schedule_time', read_only=True)
    resolution_display = serializers.CharField(source='get_resolution_display', read_only=True)

    class Meta:
        model  = WaitlistEntry
        fields = [
            'id', 'student', 'student_name', 'student_phone',
            'trip', 'trip_place', 'trip_date', 'schedule_time',
            'amount_paid', 'resolution', 'resolution_display',
            'resolution_notes', 'created_at', 'resolved_at',
            'credit_valid_until', 'alternatives_sent',
        ]
        read_only_fields = ['created_at', 'resolved_at', 'credit_valid_until']


class CreditBalanceSerializer(serializers.ModelSerializer):
    student_name = serializers.CharField(source='student.user.user_name', read_only=True)
    is_valid     = serializers.BooleanField(read_only=True)

    class Meta:
        model  = CreditBalance
        fields = ['id', 'student', 'student_name', 'balance', 'valid_until', 'is_valid', 'updated_at']


class StudentNotificationSerializer(serializers.ModelSerializer):
    class Meta:
        model  = StudentNotification
        fields = ['id', 'type', 'title_ar', 'title_en', 'body_ar', 'body_en',
                  'is_read', 'data', 'created_at']
        read_only_fields = ['created_at']
