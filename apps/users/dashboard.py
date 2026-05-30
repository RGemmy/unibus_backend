"""
Dashboard stats — add this view to apps/users/views.py
and wire it up in apps/users/urls.py
"""
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from datetime import date


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def dashboard_stats(request):
    from apps.trips.models import Trip
    from apps.students.models import Student
    from apps.buses.models import Bus
    from apps.reservations.models import TripReservation
    from apps.payments.models import Payment
    from apps.subscriptions.models import Subscription
    from django.db.models import Sum

    today = date.today()

    total_trips          = Trip.objects.count()
    today_trips          = Trip.objects.filter(trip_date=today).count()
    total_students       = Student.objects.count()
    total_buses          = Bus.objects.count()
    active_reservations  = TripReservation.objects.filter(status='confirmed').count()
    pending_payments     = Payment.objects.filter(status='pending').count()
    active_subscriptions = Subscription.objects.filter(status='active').count()

    revenue_month = (
        Payment.objects
        .filter(status='paid', created_at__year=today.year, created_at__month=today.month)
        .aggregate(total=Sum('amount'))['total'] or 0
    )

    return Response({
        'total_trips':          total_trips,
        'today_trips':          today_trips,
        'total_students':       total_students,
        'total_buses':          total_buses,
        'active_reservations':  active_reservations,
        'pending_payments':     pending_payments,
        'active_subscriptions': active_subscriptions,
        'revenue_month':        float(revenue_month),
    })
