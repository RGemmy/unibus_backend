from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from django.utils import timezone
import heapq
import hashlib
from .models import TripReservation
from .serializers import TripReservationSerializer, GPSUpdateSerializer

# ── Duplicate Detection Cache ─────────────────────────────────────────────────
# dict بسيط في الذاكرة { fingerprint: timestamp }
# في production يتحول لـ Redis
_reservation_fingerprints: dict = {}

def _make_fingerprint(student_id: int, trip_id: int) -> str:
    """
    خوارزمية Hashing لكشف طلبات الحجز المكررة.
    بتعمل hash فريد لكل (student_id, trip_id) بـ SHA-256.
    لو نفس الـ hash جه تاني مرة خلال 10 ثواني → طلب مكرر يتمنع.
    التعقيد: O(1) للـ hash + O(1) للبحث في الـ dict.
    """
    raw = f"{student_id}:{trip_id}"
    return hashlib.sha256(raw.encode()).hexdigest()


class TripReservationViewSet(viewsets.ModelViewSet):
    queryset = (TripReservation.objects
                .select_related('student__user', 'trip__place', 'trip__schedule', 'trip__bus')
                .all())
    serializer_class   = TripReservationSerializer
    permission_classes = [IsAuthenticated]
    filterset_fields   = ['status', 'trip', 'student', 'trip_type', 'scanned']
    search_fields      = ['student__user__user_name', 'trip__place__place_name']
    ordering           = ['-trip_reservation_date']

    @action(detail=False, methods=['get'], url_path='my')
    def my_reservations(self, request):
        """حجوزات الطالب نفسه (بدون الملغية)."""
        if hasattr(request.user, 'student_profile'):
            qs = self.get_queryset().filter(
                student=request.user.student_profile
            ).exclude(status='cancelled')
            serializer = self.get_serializer(qs, many=True)
            return Response(serializer.data)
        return Response([])

    def create(self, request, *args, **kwargs):
        """
        Override create لإضافة Duplicate Detection قبل الحجز.

        خوارزمية Hashing — كشف الطلبات المكررة:
          1. اعمل fingerprint = SHA-256(student_id:trip_id)
          2. لو الـ fingerprint موجود في الـ cache وفرق الوقت < 10 ثواني → ارفض
          3. لو مش موجود → احفظه في الـ cache وكمّل الحجز بشكل طبيعي
          4. نظّف الـ cache من الإدخالات القديمة (> 60 ثانية) دورياً
        """
        student_id = request.data.get('student')
        trip_id    = request.data.get('trip')

        if student_id and trip_id:
            fingerprint = _make_fingerprint(int(student_id), int(trip_id))
            now         = timezone.now().timestamp()

            # نظّف الـ cache من الإدخالات اللي عدت عليها أكتر من 60 ثانية
            expired = [k for k, t in _reservation_fingerprints.items() if now - t > 60]
            for k in expired:
                del _reservation_fingerprints[k]

            # لو الـ fingerprint موجود وفرق الوقت < 10 ثواني → مكرر
            if fingerprint in _reservation_fingerprints:
                elapsed = now - _reservation_fingerprints[fingerprint]
                if elapsed < 10:
                    return Response(
                        {'detail': 'طلب مكرر — انتظر لحظة قبل إعادة المحاولة'},
                        status=status.HTTP_429_TOO_MANY_REQUESTS
                    )

            _reservation_fingerprints[fingerprint] = now

        return super().create(request, *args, **kwargs)

    # ── Binary Search: البحث السريع عن حجز بالتاريخ ──────────────────────────
    @action(detail=False, methods=['get'], url_path='search-by-date')
    def search_by_date(self, request):
        """
        خوارزمية Binary Search للبحث عن حجوزات طالب في تاريخ معين.

        المشكلة:
          الكود العادي بيعمل Full Table Scan — بيمشي على كل الحجوزات.
          لو عندنا 10,000 حجز ده بطيء.

        الحل:
          الحجوزات مرتبة بالتاريخ (ordering = ['-trip_reservation_date']).
          نحوّل القائمة لـ list مرتبة تصاعدياً ونعمل Binary Search.

        التعقيد:
          - Full Scan:    O(n)
          - Binary Search: O(log n)  ← أسرع بكتير مع البيانات الكبيرة

        Query Params: ?target_date=2026-05-20&student_id=3
        """
        from datetime import date as date_type

        target_date_str = request.query_params.get('target_date')
        student_id      = request.query_params.get('student_id')

        if not target_date_str or not student_id:
            return Response(
                {'detail': 'target_date و student_id مطلوبين'},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            target_date = date_type.fromisoformat(target_date_str)
        except ValueError:
            return Response(
                {'detail': 'صيغة التاريخ غلط — استخدم YYYY-MM-DD'},
                status=status.HTTP_400_BAD_REQUEST
            )

        # جيب حجوزات الطالب مرتبة تصاعدياً بالتاريخ
        reservations = list(
            TripReservation.objects
            .filter(student_id=student_id)
            .select_related('trip__place', 'trip__schedule')
            .order_by('trip_reservation_date')
        )

        if not reservations:
            return Response({'detail': 'لا توجد حجوزات لهذا الطالب', 'results': []})

        # ── Binary Search ─────────────────────────────────────────────────────
        dates = [r.trip_reservation_date for r in reservations]
        lo, hi = 0, len(dates) - 1
        first_idx = -1

        while lo <= hi:
            mid = (lo + hi) // 2
            if dates[mid] == target_date:
                first_idx = mid
                hi = mid - 1       # كمّل شمالاً عشان تلاقي أول تكرار
            elif dates[mid] < target_date:
                lo = mid + 1
            else:
                hi = mid - 1

        if first_idx == -1:
            return Response({
                'target_date': target_date_str,
                'results':     [],
                'algorithm':   'Binary Search — O(log n)',
            })

        # اجمع كل الحجوزات في نفس التاريخ
        matched = []
        idx = first_idx
        while idx < len(reservations) and reservations[idx].trip_reservation_date == target_date:
            r = reservations[idx]
            matched.append({
                'reservation_id': r.id,
                'trip_place':     r.trip.place.place_name,
                'trip_time':      str(r.trip.schedule.schedule_time),
                'status':         r.status,
                'trip_type':      r.trip_type,
                'scanned':        r.scanned,
            })
            idx += 1

        return Response({
            'target_date':    target_date_str,
            'total_found':    len(matched),
            'algorithm':      'Binary Search — O(log n)',
            'searched_in':    len(reservations),
            'results':        matched,
        })

    @action(detail=True, methods=['delete'], url_path='cancel')
    def cancel(self, request, pk=None):
        """الطالب يلغي حجزه."""
        reservation = self.get_object()
        reservation.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(detail=True, methods=['patch'], url_path='confirm')
    def confirm(self, request, pk=None):
        """الطالب يؤكد حجزه (بعد الدفع)."""
        reservation = self.get_object()
        reservation.status = 'confirmed'
        reservation.save()
        return Response(self.get_serializer(reservation).data)

    # ── QR Scan (المشرف يسكن الطالب) ─────────────────────────────────────────
    @action(detail=True, methods=['patch'], url_path='scan')
    def scan(self, request, pk=None):
        """
        المشرف يسكن QR الطالب عند الركوب.
        يغير scanned=True و status='confirmed'.
        """
        reservation = self.get_object()
        if reservation.scanned:
            return Response(
                {'detail': 'تم تسجيل الحضور مسبقاً', 'scanned_at': reservation.scanned_at},
                status=status.HTTP_200_OK
            )
        reservation.mark_scanned()
        return Response({
            'detail': 'تم تسجيل الحضور بنجاح ✅',
            'student_name': reservation.student.user.user_name,
            'seat_number':  reservation.seat_number,
            'scanned_at':   reservation.scanned_at,
        })

    # ── Priority Queue: ترتيب طوابير الحجز بالأولوية ─────────────────────────
    @action(detail=False, methods=['get'], url_path='priority-queue')
    def priority_queue(self, request):
        """
        خوارزمية Priority Queue لترتيب طلبات الحجز المعلقة حسب الأولوية.

        معايير الأولوية (الأعلى = الأهم):
          3 نقاط — الطالب عنده اشتراك فعّال (Subscription)
          2 نقاط — الطالب حجز من قبل ورجع (له حجوزات سابقة مكتملة)
          1 نقطة  — حجز ذهاب (go) أولى من العودة (return)
          0 نقاط  — باقي الحجوزات

        الخوارزمية:
          - نبني min-heap بقيم سالبة عشان نعمل max-heap
          - كل عنصر: (-priority, reservation_date, reservation_id)
          - نرجع القائمة مرتبة من الأعلى أولوية للأدنى
        """
        trip_id = request.query_params.get('trip_id')
        if not trip_id:
            return Response(
                {'detail': 'trip_id مطلوب كـ query parameter'},
                status=status.HTTP_400_BAD_REQUEST
            )

        # جيب كل الحجوزات المعلقة للرحلة دي
        pending_reservations = (
            TripReservation.objects
            .filter(trip_id=trip_id, status__in=['pending', 'pending_confirm'])
            .select_related('student__user', 'student__subscriptions')
            .prefetch_related('student__reservations')
        )

        if not pending_reservations.exists():
            return Response({'detail': 'لا توجد حجوزات معلقة لهذه الرحلة', 'queue': []})

        heap = []

        for res in pending_reservations:
            priority = 0

            # +3 لو عنده اشتراك فعّال
            has_active_sub = res.student.subscriptions.filter(status='active').exists()
            if has_active_sub:
                priority += 3

            # +2 لو حجز قبل كده وخلّص الرحلة (scanned)
            prev_completed = res.student.reservations.filter(
                scanned=True
            ).exclude(id=res.id).exists()
            if prev_completed:
                priority += 2

            # +1 لو رحلة ذهاب
            if res.trip_type == 'go':
                priority += 1

            # min-heap بقيم سالبة = max-heap
            # التعادل في الأولوية → الأقدم في الحجز يتقدم
            heapq.heappush(heap, (-priority, res.trip_reservation_date.toordinal(), res.id))

        # استخرج العناصر مرتبة
        sorted_queue = []
        rank = 1
        while heap:
            neg_priority, _, res_id = heapq.heappop(heap)
            res = next(r for r in pending_reservations if r.id == res_id)
            sorted_queue.append({
                'rank':            rank,
                'reservation_id':  res.id,
                'student_name':    res.student.user.user_name,
                'trip_type':       res.trip_type,
                'status':          res.status,
                'priority_score':  -neg_priority,
                'reserved_on':     res.trip_reservation_date,
            })
            rank += 1

        return Response({
            'trip_id':    trip_id,
            'total':      len(sorted_queue),
            'queue':      sorted_queue,
        })

    # ── GPS: الطالب يشير موقعه ────────────────────────────────────────────────
    @action(detail=True, methods=['patch'], url_path='update-gps')
    def update_gps(self, request, pk=None):
        """
        الطالب يبعت موقعه الحالي عشان السائق والمشرف يشوفوه.

        Body المطلوب:
          { "latitude": 31.2001, "longitude": 29.9187 }

        ملاحظات:
          - بس الطالب صاحب الحجز هو اللي يقدر يحدّث موقعه.
          - gps_sharing بتتحول تلقائياً لـ True عند أول تحديث.
          - gps_updated_at بيتسجل وقت التحديث الأخير.
        """
        reservation = self.get_object()

        # تأكد إن الطالب ده هو صاحب الحجز
        if hasattr(request.user, 'student_profile'):
            if reservation.student != request.user.student_profile:
                return Response(
                    {'detail': 'مش مسموح — ده مش حجزك'},
                    status=status.HTTP_403_FORBIDDEN
                )
        else:
            return Response(
                {'detail': 'مش مسموح — الأكاونت ده مش طالب'},
                status=status.HTTP_403_FORBIDDEN
            )

        serializer = GPSUpdateSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        lat = serializer.validated_data['latitude']
        lng = serializer.validated_data['longitude']

        reservation.update_gps(lat, lng)

        return Response({
            'detail':      'تم تحديث الموقع ✅',
            'latitude':    str(lat),
            'longitude':   str(lng),
            'updated_at':  reservation.gps_updated_at,
            'maps_link':   f'https://maps.google.com/?q={lat},{lng}',
        })

    @action(detail=True, methods=['patch'], url_path='stop-gps')
    def stop_gps(self, request, pk=None):
        """
        الطالب يوقف مشاركة موقعه.
        بيخلي gps_sharing = False.
        """
        reservation = self.get_object()

        if hasattr(request.user, 'student_profile'):
            if reservation.student != request.user.student_profile:
                return Response(
                    {'detail': 'مش مسموح — ده مش حجزك'},
                    status=status.HTTP_403_FORBIDDEN
                )
        else:
            return Response(
                {'detail': 'مش مسموح — الأكاونت ده مش طالب'},
                status=status.HTTP_403_FORBIDDEN
            )

        reservation.stop_gps_sharing()
        return Response({'detail': 'تم إيقاف مشاركة الموقع 🔴'})

    @action(detail=False, methods=['get'], url_path='trip-gps')
    def trip_gps(self, request):
        """
        السائق أو المشرف يشوف مواقع كل الطلاب في رحلة معينة.

        Query Params: ?trip_id=5
        بيرجع بس الطلاب اللي gps_sharing=True وحدّثوا موقعهم.
        """
        trip_id = request.query_params.get('trip_id')
        if not trip_id:
            return Response(
                {'detail': 'trip_id مطلوب كـ query parameter'},
                status=status.HTTP_400_BAD_REQUEST
            )

        # جيب الحجوزات اللي فعّلت GPS Sharing
        reservations = (
            TripReservation.objects
            .filter(trip_id=trip_id, gps_sharing=True)
            .exclude(gps_latitude=None)
            .select_related('student__user')
            .order_by('-gps_updated_at')
        )

        students_locations = []
        for res in reservations:
            # تحقق إن الموقع محدّث خلال آخر 10 دقايق
            if res.gps_updated_at:
                age_seconds = (timezone.now() - res.gps_updated_at).total_seconds()
                is_fresh = age_seconds < 600   # 10 دقايق
            else:
                is_fresh = False

            students_locations.append({
                'reservation_id': res.id,
                'student_name':   res.student.user.user_name,
                'seat_number':    res.seat_number,
                'latitude':       str(res.gps_latitude),
                'longitude':      str(res.gps_longitude),
                'updated_at':     res.gps_updated_at,
                'is_fresh':       is_fresh,   # موقع حي (< 10 دقايق)؟
                'maps_link':      f'https://maps.google.com/?q={res.gps_latitude},{res.gps_longitude}',
            })

        return Response({
            'trip_id':          trip_id,
            'sharing_students': len(students_locations),
            'locations':        students_locations,
        })

    # ── Scan by QR token (بدون ID) ────────────────────────────────────────────
    @action(detail=False, methods=['post'], url_path='scan-qr')
    def scan_qr(self, request):
        """
        المشرف يبعت { reservation_id, trip_id } من QR.
        """
        res_id  = request.data.get('reservation_id')
        trip_id = request.data.get('trip_id')
        try:
            reservation = TripReservation.objects.select_related(
                'student__user', 'trip'
            ).get(id=res_id, trip_id=trip_id)
        except TripReservation.DoesNotExist:
            return Response({'detail': 'حجز غير موجود أو QR غير صالح'},
                            status=status.HTTP_404_NOT_FOUND)

        if reservation.status == 'cancelled':
            return Response({'detail': 'الحجز ملغي'}, status=status.HTTP_400_BAD_REQUEST)

        if reservation.scanned:
            return Response({
                'detail': 'تم التسجيل مسبقاً',
                'student_name': reservation.student.user.user_name,
                'scanned_at': reservation.scanned_at,
            })

        reservation.mark_scanned()
        return Response({
            'detail':       'تم تسجيل الحضور ✅',
            'student_name': reservation.student.user.user_name,
            'seat_number':  reservation.seat_number,
            'trip_type':    reservation.trip_type,
            'scanned_at':   reservation.scanned_at,
        })
