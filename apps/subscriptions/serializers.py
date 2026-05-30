from rest_framework import serializers
from .models import Subscription

class SubscriptionSerializer(serializers.ModelSerializer):
    student_name = serializers.CharField(source='student.user.user_name', read_only=True)

    class Meta:
        model  = Subscription
        fields = ['id', 'student', 'student_name', 'status', 'start_date', 'end_date', 'plan', 'amount']
