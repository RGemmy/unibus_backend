from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from django.utils import timezone
from django.db.models import Q

from .models import WaitlistEntry, CreditBalance, StudentNotification
from .serializers import WaitlistEntrySerializer, CreditBalanceSerializer, StudentNotificationSerializer
from apps.trips.models import Trip


class WaitlistViewSet(viewsets.ModelViewSet):
    """
    قائمة الانتظار — يستخدمها المشرف لعرض الطلاب الغايبين
    والطالب لاختيار الحل (استرداد أو رصيد).
    """
    queryset = (WaitlistEntry.objects
                .select_related('student__user', 'trip__place', 'trip__schedule')
                .all())
    serializer_class   = WaitlistEntrySerializer
    permission_classes = [IsAuthenticated]
    filterset_fields   = ['resolution', 'trip', 'student', 'alternatives_sent']

    def get_queryset(self):
        qs = super().get_queryset()
        user = self.request.user
        # الطالب يشوف إدخالاته فقط
        if hasattr(user, 'student_profile'):
            return qs.filter(student=user.student_profile)
        return qs

    # ── المشرف: إرسال مواعيد الرحلات البديلة للطالب (مرتبة بخوارزمية) ────────
    @action(detail=True, methods=['post'], url_path='send-alternatives')
    def send_alternatives(self, request, pk=None):
        entry = self.get_object()
        if entry.alternatives_sent:
            return Response({'detail': 'تم الإرسال مسبقاً'}, status=400)

        # جيب رحلات تانية في نفس اليوم
        alternatives = Trip.objects.filter(
            trip_date=entry.trip.trip_date,
            status='active',
        ).exclude(id=entry.trip.id).select_related('place', 'schedule')

        # ── خوارزمية Multi-key Sorting للرحلات البديلة ──────────────────────
        #
        # المشكلة: الكود القديم كان بيرجع الرحلات بدون ترتيب — الطالب مش عارف
        #          أنهي رحلة أحسنه يختار.
        #
        # الحل: نرتب بـ 3 معايير بالترتيب ده:
        #   1. المقاعد المتاحة (available_seats) — الأكثر مقاعد أولاً
        #   2. وقت الرحلة (schedule_time)        — الأقرب لوقت الرحلة الأصلية أولاً
        #   3. اسم المكان (place_name)            — أبجدياً كـ tiebreaker
        #
        # التعقيد الزمني: O(n log n) — Python بيستخدم Timsort
        # ──────────────────────────────────────────────────────────────────────
        from datetime import datetime

        original_time = entry.trip.schedule.schedule_time

        def sort_key(trip):
            # فرق الوقت بالثواني بين الرحلة البديلة والرحلة الأصلية
            t1 = datetime.combine(datetime.today(), trip.schedule.schedule_time)
            t2 = datetime.combine(datetime.today(), original_time)
            time_diff = abs((t1 - t2).total_seconds())

            return (
                -trip.available_seats,   # المقاعد: الأكثر أولاً (سالب عشان نعكس الترتيب)
                time_diff,               # الوقت: الأقرب أولاً
                trip.place.place_name,   # الاسم: أبجدي كـ tiebreaker
            )

        sorted_alternatives = sorted(alternatives, key=sort_key)

        alt_list = [
            {
                'id':              t.id,
                'place':           t.place.place_name,
                'time':            str(t.schedule.schedule_time),
                'available_seats': t.available_seats,
                'sort_score':      {
                    'seats':     t.available_seats,
                    'time_diff': abs((
                        datetime.combine(datetime.today(), t.schedule.schedule_time) -
                        datetime.combine(datetime.today(), original_time)
                    ).total_seconds()),
                },
            }
            for t in sorted_alternatives
        ]

        body_ar = f"عزيزي الطالب، غبت عن رحلة {entry.trip.place.place_name} بتاريخ {entry.trip.trip_date}.\n"
        body_en = f"Dear student, you missed the trip to {entry.trip.place.place_name} on {entry.trip.trip_date}.\n"

        if alt_list:
            body_ar += "الرحلات المتاحة في نفس اليوم:\n" + "\n".join(
                f"• {a['place']} — الساعة {a['time']} ({a['available_seats']} مقعد متاح)" for a in alt_list
            )
            body_en += "Available trips today:\n" + "\n".join(
                f"• {a['place']} at {a['time']} ({a['available_seats']} seats available)" for a in alt_list
            )
        else:
            body_ar += "لا توجد رحلات بديلة متاحة في هذا اليوم."
            body_en += "No alternative trips available on this day."

        StudentNotification.objects.create(
            student   = entry.student,
            type      = 'alternatives',
            title_ar  = 'رحلات بديلة متاحة',
            title_en  = 'Alternative trips available',
            body_ar   = body_ar,
            body_en   = body_en,
            data      = {'alternatives': alt_list, 'waitlist_entry_id': entry.id,
                         'amount_paid': str(entry.amount_paid)},
        )

        entry.alternatives_sent = True
        entry.save()
        return Response({'detail': 'تم الإرسال', 'alternatives_count': len(alt_list)})

    # ── الطالب: اختيار استرداد ───────────────────────────────────────────────
    @action(detail=True, methods=['post'], url_path='choose-refund')
    def choose_refund(self, request, pk=None):
        entry = self.get_object()
        if entry.resolution != 'pending':
            return Response({'detail': 'تم اختيار الحل مسبقاً'}, status=400)

        entry.resolve_refund()

        StudentNotification.objects.create(
            student  = entry.student,
            type     = 'refund_initiated',
            title_ar = 'طلب استرداد المبلغ',
            title_en = 'Refund requested',
            body_ar  = f'سيتم رد مبلغ {entry.amount_paid} ج.م خلال 24 ساعة.',
            body_en  = f'Your refund of {entry.amount_paid} EGP will be processed within 24 hours.',
            data     = {'amount': str(entry.amount_paid), 'waitlist_entry_id': entry.id},
        )
        return Response(WaitlistEntrySerializer(entry).data)

    # ── الطالب: اختيار رصيد لرحلة تانية ────────────────────────────────────
    @action(detail=True, methods=['post'], url_path='choose-credit')
    def choose_credit(self, request, pk=None):
        entry = self.get_object()
        if entry.resolution != 'pending':
            return Response({'detail': 'تم اختيار الحل مسبقاً'}, status=400)

        entry.resolve_credit()

        StudentNotification.objects.create(
            student  = entry.student,
            type     = 'credit_added',
            title_ar = 'تم إضافة رصيد',
            title_en = 'Credit added',
            body_ar  = (f'تم إضافة {entry.amount_paid} ج.م كرصيد لحجز رحلة أخرى '
                        f'صالح حتى {entry.credit_valid_until}.'),
            body_en  = (f'{entry.amount_paid} EGP credit added for another trip, '
                        f'valid until {entry.credit_valid_until}.'),
            data     = {'amount': str(entry.amount_paid),
                        'valid_until': str(entry.credit_valid_until),
                        'waitlist_entry_id': entry.id},
        )
        return Response(WaitlistEntrySerializer(entry).data)


class StudentNotificationViewSet(viewsets.ReadOnlyModelViewSet):
    """إشعارات الطالب — قراءة + تحديد كمقروء"""
    serializer_class   = StudentNotificationSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        if hasattr(user, 'student_profile'):
            return StudentNotification.objects.filter(student=user.student_profile)
        return StudentNotification.objects.none()

    @action(detail=True, methods=['patch'], url_path='mark-read')
    def mark_read(self, request, pk=None):
        notif = self.get_object()
        notif.is_read = True
        notif.save()
        return Response({'status': 'ok'})

    @action(detail=False, methods=['patch'], url_path='mark-all-read')
    def mark_all_read(self, request):
        self.get_queryset().filter(is_read=False).update(is_read=True)
        return Response({'status': 'ok'})

    @action(detail=False, methods=['get'], url_path='unread-count')
    def unread_count(self, request):
        count = self.get_queryset().filter(is_read=False).count()
        return Response({'count': count})


class CreditBalanceViewSet(viewsets.ReadOnlyModelViewSet):
    """رصيد الطالب"""
    serializer_class   = CreditBalanceSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        if hasattr(user, 'student_profile'):
            return CreditBalance.objects.filter(student=user.student_profile)
        # المشرف يشوف الكل
        return CreditBalance.objects.select_related('student__user').all()

    @action(detail=False, methods=['get'], url_path='mine')
    def mine(self, request):
        user = request.user
        if not hasattr(user, 'student_profile'):
            return Response({'balance': 0, 'valid_until': None, 'is_valid': False})
        try:
            cb = CreditBalance.objects.get(student=user.student_profile)
            return Response(CreditBalanceSerializer(cb).data)
        except CreditBalance.DoesNotExist:
            return Response({'balance': 0, 'valid_until': None, 'is_valid': False})
