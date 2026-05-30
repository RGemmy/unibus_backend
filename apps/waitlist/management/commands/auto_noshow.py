"""
management command: auto_noshow
================================
يُشغَّل بـ cron كل 5 دقائق:
    */5 * * * * python manage.py auto_noshow

المنطق:
  - كل رحلة اليوم بدأت منذ أكثر من 15 دقيقة (schedule_time + 15 min < now)
  - والحجز confirmed لكن ما اتعملوش scan (scanned=False)
  - → أضفه على قائمة الانتظار + ابعتله إشعار + غيّر status الحجز لـ no_show
"""
from django.core.management.base import BaseCommand
from django.utils import timezone
from datetime import datetime, timedelta

from apps.trips.models import Trip
from apps.reservations.models import TripReservation
from apps.waitlist.models import WaitlistEntry, StudentNotification


class Command(BaseCommand):
    help = 'اكشف الطلاب الغايبين بعد انطلاق الرحلة وأضفهم لقائمة الانتظار'

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run', action='store_true',
            help='عرض فقط بدون تغيير في قاعدة البيانات'
        )

    def handle(self, *args, **options):
        dry_run = options['dry_run']
        now     = timezone.localtime()
        today   = now.date()
        cutoff  = (now - timedelta(minutes=15)).time()  # الرحلات اللي بدأت منذ 15+ دقيقة

        self.stdout.write(f'[auto_noshow] {now.strftime("%Y-%m-%d %H:%M")} — checking...')

        # رحلات اليوم النشطة أو المكتملة اللي schedule_time < cutoff
        trips_to_check = Trip.objects.filter(
            trip_date=today,
            status__in=['active', 'completed'],
            schedule__schedule_time__lte=cutoff,
        ).select_related('place', 'schedule', 'bus')

        total_added = 0

        for trip in trips_to_check:
            # حجوزات مؤكدة لم يُعمل لها scan
            no_show_reservations = TripReservation.objects.filter(
                trip=trip,
                status='confirmed',
                scanned=False,          # الحقل اللي هنضيفه على TripReservation
            ).select_related('student__user')

            for res in no_show_reservations:
                # تجنّب التكرار
                if WaitlistEntry.objects.filter(student=res.student, trip=trip).exists():
                    continue

                # جيب المبلغ المدفوع من الـ payment لو موجود
                amount = 0
                try:
                    from apps.payments.models import Payment
                    payment = Payment.objects.filter(
                        reservation=res, status='paid'
                    ).first()
                    if payment:
                        amount = payment.amount
                except Exception:
                    pass

                if not dry_run:
                    # 1. أضف لقائمة الانتظار
                    WaitlistEntry.objects.create(
                        student     = res.student,
                        trip        = trip,
                        reservation = res,
                        amount_paid = amount,
                    )

                    # 2. غيّر status الحجز
                    res.status = 'no_show'
                    res.save(update_fields=['status'])

                    # 3. ابعت إشعار للطالب
                    StudentNotification.objects.create(
                        student  = res.student,
                        type     = 'no_show',
                        title_ar = '⚠️ لم تحضر الرحلة',
                        title_en = '⚠️ You missed your trip',
                        body_ar  = (
                            f'لم يتم تسجيل حضورك في رحلة {trip.place.place_name} '
                            f'بتاريخ {trip.trip_date} الساعة {trip.schedule.schedule_time}. '
                            f'سيتواصل معك المشرف بخصوص خياراتك.'
                        ),
                        body_en  = (
                            f'You were not scanned for the trip to {trip.place.place_name} '
                            f'on {trip.trip_date} at {trip.schedule.schedule_time}. '
                            f'A supervisor will contact you about your options.'
                        ),
                        data = {
                            'trip_id':    trip.id,
                            'trip_place': trip.place.place_name,
                            'trip_date':  str(trip.trip_date),
                            'amount_paid': str(amount),
                        },
                    )

                    total_added += 1
                    self.stdout.write(
                        self.style.WARNING(
                            f'  ➕ no-show: {res.student.user.user_name} — {trip.place.place_name} {trip.trip_date}'
                        )
                    )
                else:
                    self.stdout.write(
                        f'  [DRY] would add: {res.student.user.user_name} — {trip}'
                    )

        self.stdout.write(
            self.style.SUCCESS(f'[auto_noshow] done — {total_added} entries added.')
        )
