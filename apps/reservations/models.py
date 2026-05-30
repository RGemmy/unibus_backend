from django.db import models
from django.utils import timezone
from apps.students.models import Student
from apps.trips.models import Trip


class TripReservation(models.Model):
    STATUS_CHOICES = [
        ('pending',         'معلقة'),
        ('pending_confirm', 'بانتظار التأكيد'),
        ('confirmed',       'مؤكدة'),
        ('cancelled',       'ملغية'),
        ('no_show',         'لم يحضر'),
    ]
    student               = models.ForeignKey(Student, on_delete=models.CASCADE, related_name='reservations')
    trip                  = models.ForeignKey(Trip,    on_delete=models.CASCADE, related_name='reservations')
    trip_reservation_date = models.DateField(auto_now_add=True)
    status                = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')

    # ── QR scan ──────────────────────────────────────────────────────────────
    scanned    = models.BooleanField(default=False)
    scanned_at = models.DateTimeField(null=True, blank=True)

    # ── مهلة التأكيد ─────────────────────────────────────────────────────────
    confirm_deadline = models.DateTimeField(null=True, blank=True)
    reminder_sent    = models.BooleanField(default=False)

    # ── GPS Location (الطالب يشير موقعه) ─────────────────────────────────────
    gps_latitude    = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    gps_longitude   = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    gps_updated_at  = models.DateTimeField(null=True, blank=True)
    gps_sharing     = models.BooleanField(default=False)   # الطالب فعّل المشاركة؟

    # ── بيانات إضافية ────────────────────────────────────────────────────────
    seat_number     = models.PositiveSmallIntegerField(null=True, blank=True)
    trip_type       = models.CharField(
        max_length=10, blank=True, default='go',
        choices=[('go', 'ذهاب'), ('return', 'عودة')]
    )
    payment_method  = models.CharField(max_length=20, blank=True)
    payment_receipt = models.TextField(blank=True)   # base64 أو URL

    class Meta:
        db_table        = 'trip_reservations'
        unique_together = [('student', 'trip')]
        ordering        = ['-trip_reservation_date']

    def __str__(self):
        return f"{self.student} — {self.trip}"

    # ── helper: تحديث GPS ────────────────────────────────────────────────────
    def update_gps(self, latitude, longitude):
        from django.utils import timezone
        self.gps_latitude   = latitude
        self.gps_longitude  = longitude
        self.gps_updated_at = timezone.now()
        self.gps_sharing    = True
        self.save(update_fields=['gps_latitude', 'gps_longitude', 'gps_updated_at', 'gps_sharing'])

    # ── helper: إيقاف مشاركة GPS ─────────────────────────────────────────────
    def stop_gps_sharing(self):
        self.gps_sharing = False
        self.save(update_fields=['gps_sharing'])

    # ── helper: تسجيل الحضور ─────────────────────────────────────────────────
    def mark_scanned(self):
        self.scanned    = True
        self.scanned_at = timezone.now()
        self.status     = 'confirmed'
        self.save(update_fields=['scanned', 'scanned_at', 'status'])
