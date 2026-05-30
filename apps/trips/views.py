from rest_framework import viewsets, status
from rest_framework.decorators import action, api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from django.db.models import Count, Sum
from django.utils import timezone
from .models import Trip
from .serializers import TripSerializer


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def dashboard_stats(request):
    from apps.students.models import Student
    from apps.reservations.models import TripReservation
    from apps.payments.models import Payment
    from apps.buses.models import Bus
    from apps.subscriptions.models import Subscription

    today = timezone.now().date()
    month_start = today.replace(day=1)

    stats = {
        'total_trips':          Trip.objects.count(),
        'today_trips':          Trip.objects.filter(trip_date=today).count(),
        'active_reservations':  TripReservation.objects.filter(status__in=['confirmed','pending']).count(),
        'total_students':       Student.objects.count(),
        'total_buses':          Bus.objects.count(),
        'active_subscriptions': Subscription.objects.filter(status='active').count(),
        'pending_payments':     Payment.objects.filter(status='pending').count(),
        'revenue_month':        Payment.objects.filter(
            status='paid', created_at__gte=month_start
        ).aggregate(total=Sum('amount'))['total'] or 0,
    }
    return Response(stats)


class TripViewSet(viewsets.ModelViewSet):
    queryset = Trip.objects.select_related(
        'place', 'bus', 'schedule', 'schedule__route'
    ).all()
    serializer_class   = TripSerializer
    permission_classes = [IsAuthenticated]
    filterset_fields   = ['status', 'trip_date', 'place', 'bus']
    search_fields      = ['place__place_name', 'bus__plate_number']
    ordering_fields    = ['trip_date', 'created_at']
    ordering           = ['-trip_date']

    @action(detail=True, methods=['patch'])
    def change_status(self, request, pk=None):
        trip   = self.get_object()
        new_st = request.data.get('status')
        valid  = [c[0] for c in Trip.STATUS_CHOICES]
        if new_st not in valid:
            return Response({'error': 'حالة غير صالحة'}, status=status.HTTP_400_BAD_REQUEST)
        trip.status = new_st
        trip.save()
        return Response(TripSerializer(trip).data)

    # ── Greedy Algorithm: توزيع الطلاب على الأتوبيسات ────────────────────────
    @action(detail=False, methods=['post'], url_path='assign-buses')
    def assign_buses(self, request):
        """
        خوارزمية Greedy لتوزيع الطلاب على الأتوبيسات في يوم معين.

        المشكلة:
          عندنا عدد طلاب محجوزين في يوم معين وعدد أتوبيسات متاحة،
          عايزين نوزع الطلاب على أقل عدد ممكن من الأتوبيسات
          مع ضمان إن كل أتوبيس ميتعداش طاقته.

        الخوارزمية (Greedy — First Fit Decreasing):
          1. رتّب الأتوبيسات تنازلياً حسب الطاقة (الأكبر أولاً)
          2. رتّب الطلاب تنازلياً حسب الأولوية (المشتركين أولاً)
          3. لكل طالب: حطّه في أول أتوبيس عنده مكان
          4. لو مفيش أتوبيس فيه مكان → الطالب في قائمة الانتظار

        التعقيد الزمني: O(n × m) — n طلاب، m أتوبيسات
        النتيجة المثلى: مش مضمونة 100% (ده طبيعي في Greedy)،
                        لكن عملياً بتوصل لحل كويس جداً بسرعة.

        Body المطلوب: { "trip_date": "2026-05-20" }
        """
        from apps.students.models import Student
        from apps.buses.models import Bus
        from apps.reservations.models import TripReservation

        trip_date = request.data.get('trip_date')
        if not trip_date:
            return Response(
                {'detail': 'trip_date مطلوب'},
                status=status.HTTP_400_BAD_REQUEST
            )

        # جيب الرحلات النشطة في اليوم ده
        trips_today = Trip.objects.filter(
            trip_date=trip_date,
            status__in=['pending', 'active']
        ).select_related('bus')

        if not trips_today.exists():
            return Response({'detail': 'لا توجد رحلات في هذا اليوم'})

        # جيب كل الحجوزات المؤكدة للرحلات دي
        reservations = (
            TripReservation.objects
            .filter(trip__in=trips_today, status__in=['confirmed', 'pending_confirm'])
            .select_related('student__user', 'student__subscriptions', 'trip__bus')
        )

        # ── Step 1: رتّب الأتوبيسات تنازلياً حسب الطاقة ──────────────────────
        buses = sorted(
            set(t.bus for t in trips_today),
            key=lambda b: b.capacity,
            reverse=True
        )

        # ── Step 2: رتّب الطلاب حسب الأولوية (مشترك أولاً) ──────────────────
        def student_priority(res):
            has_sub = res.student.subscriptions.filter(status='active').exists()
            return (0 if has_sub else 1, res.trip_reservation_date)

        sorted_reservations = sorted(reservations, key=student_priority)

        # ── Step 3: Greedy Assignment ─────────────────────────────────────────
        # bus_load = { bus_id: عدد الطلاب المخصصين حالياً }
        bus_load    = {b.id: 0 for b in buses}
        assignments = []   # [ {student, bus, seat_number} ]
        waitlisted  = []   # طلاب مش لاقيين مكان

        for res in sorted_reservations:
            assigned = False
            for bus in buses:
                if bus_load[bus.id] < bus.capacity:
                    bus_load[bus.id] += 1
                    seat_num = bus_load[bus.id]
                    assignments.append({
                        'reservation_id': res.id,
                        'student_name':   res.student.user.user_name,
                        'bus':            bus.plate_number,
                        'seat_number':    seat_num,
                        'has_subscription': res.student.subscriptions.filter(status='active').exists(),
                    })
                    # حدّث رقم المقعد في قاعدة البيانات
                    res.seat_number = seat_num
                    res.save(update_fields=['seat_number'])
                    assigned = True
                    break

            if not assigned:
                waitlisted.append({
                    'reservation_id': res.id,
                    'student_name':   res.student.user.user_name,
                })

        # ── Step 4: إحصائيات التوزيع ─────────────────────────────────────────
        buses_used = [
            {
                'bus':           b.plate_number,
                'capacity':      b.capacity,
                'assigned':      bus_load[b.id],
                'utilization':   f"{round(bus_load[b.id] / b.capacity * 100)}%",
            }
            for b in buses if bus_load[b.id] > 0
        ]

        return Response({
            'trip_date':       trip_date,
            'total_students':  len(sorted_reservations),
            'total_assigned':  len(assignments),
            'total_waitlisted': len(waitlisted),
            'buses_used':      buses_used,
            'assignments':     assignments,
            'waitlisted':      waitlisted,
        })
