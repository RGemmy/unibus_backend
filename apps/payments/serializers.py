from rest_framework import serializers
from .models import Payment, PaymentType

class PaymentTypeSerializer(serializers.ModelSerializer):
    class Meta:
        model  = PaymentType
        fields = '__all__'

class PaymentSerializer(serializers.ModelSerializer):
    student_name      = serializers.CharField(source='trip_reservation.student.user.user_name', read_only=True)
    trip_place        = serializers.CharField(source='trip_reservation.trip.place.place_name',  read_only=True)
    payment_type_name = serializers.CharField(source='payment_type.payment_type_name',          read_only=True)

    class Meta:
        model  = Payment
        fields = [
            'id', 'trip_reservation', 'student_name', 'trip_place',
            'payment_type', 'payment_type_name', 'amount', 'status',
            'paid_at', 'created_at',
        ]
        read_only_fields = ['created_at']
