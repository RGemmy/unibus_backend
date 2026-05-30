"""
management command: send_confirm_reminders
==========================================
يُشغَّل بـ cron كل 5 دقائق:
    */5 * * * * python manage.py send_confirm_reminders

المنطق:
  - كل حجز pending_confirm وعنده confirm_deadline
  - لو الـ deadline بيجي خلال 30 دقيقة (بس لسه ما جاش)
  - ولم يُرسل له تذكير قبل كده (reminder_sent=False)
  - → ابعتله إشعار
"""
from django.core.management.base import BaseCommand
from django.utils import timezone
from datetime import timedelta

from apps.reservations.models import TripReservation
from apps.waitlist.models import StudentNotification


class Command(BaseCommand):
    help = 'ابعت تذكير للطلاب اللي مهلة تأكيدهم هتنتهي خلال 30 دقيقة'

    def handle(self, *args, **options):
        now          = timezone.now()
        window_start = now
        window_end   = now + timedelta(minutes=30)

        self.stdout.write(f'[send_confirm_reminders] {now.strftime("%H:%M")} — checking...')

        # حجوزات pending_confirm — deadline خلال 30 دقيقة — لم يُرسل لها تذكير
        pending = TripReservation.objects.filter(
            status='pending_confirm',
            confirm_deadline__gte=window_start,
            confirm_deadline__lte=window_end,
            reminder_sent=False,        # الحقل اللي هنضيفه
        ).select_related('student__user', 'trip__place', 'trip__schedule')

        count = 0
        for res in pending:
            minutes_left = int((res.confirm_deadline - now).total_seconds() / 60)

            StudentNotification.objects.create(
                student  = res.student,
                type     = 'confirm_reminder',
                title_ar = '⏰ أكّد حجزك الآن!',
                title_en = '⏰ Confirm your booking now!',
                body_ar  = (
                    f'تبقّى {minutes_left} دقيقة فقط لتأكيد حجزك في رحلة '
                    f'{res.trip.place.place_name} الساعة {res.trip.schedule.schedule_time}. '
                    f'بعد انتهاء المهلة سيُلغى الحجز تلقائياً.'
                ),
                body_en  = (
                    f'Only {minutes_left} minutes left to confirm your booking for '
                    f'{res.trip.place.place_name} at {res.trip.schedule.schedule_time}. '
                    f'Your booking will be auto-cancelled after the deadline.'
                ),
                data = {
                    'reservation_id':   res.id,
                    'trip_id':          res.trip.id,
                    'confirm_deadline': res.confirm_deadline.isoformat(),
                    'minutes_left':     minutes_left,
                },
            )

            res.reminder_sent = True
            res.save(update_fields=['reminder_sent'])
            count += 1
            self.stdout.write(
                self.style.WARNING(
                    f'  📨 reminder → {res.student.user.user_name} '
                    f'({minutes_left} min left)'
                )
            )

        self.stdout.write(
            self.style.SUCCESS(f'[send_confirm_reminders] done — {count} reminders sent.')
        )
