from django.db import models
from django.utils import timezone
from apps.students.models import Student
from apps.trips.models import Trip
from apps.reservations.models import TripReservation


class WaitlistEntry(models.Model):
    """
    طالب حجز ودفع لكن ما ركبش — يُضاف أوتوماتيك بعد انتهاء الرحلة
    لو ما اتعملوش scan.
    """
    RESOLUTION_CHOICES = [
        ('pending',  'بانتظار اختيار الطالب'),
        ('refund',   'استرداد المبلغ'),
        ('credit',   'رصيد لرحلة تانية'),
        ('resolved', 'تم الحل'),
    ]

    student     = models.ForeignKey(Student, on_delete=models.CASCADE, related_name='waitlist_entries')
    trip        = models.ForeignKey(Trip, on_delete=models.CASCADE, related_name='waitlist_entries')
    reservation = models.OneToOneField(TripReservation, on_delete=models.CASCADE,
                                       related_name='waitlist_entry', null=True, blank=True)
    amount_paid = models.DecimalField(max_digits=8, decimal_places=2, default=0)

    # الطالب اختار إيه؟
    resolution       = models.CharField(max_length=20, choices=RESOLUTION_CHOICES, default='pending')
    resolution_notes = models.TextField(blank=True)

    # تواريخ
    created_at  = models.DateTimeField(auto_now_add=True)
    resolved_at = models.DateTimeField(null=True, blank=True)

    # الرحلة البديلة (لو اختار credit)
    credit_valid_until = models.DateField(null=True, blank=True)   # أسبوع من تاريخ الرحلة
    credit_used_trip   = models.ForeignKey(Trip, null=True, blank=True,
                                           on_delete=models.SET_NULL,
                                           related_name='used_credits')

    # إشعار اتبعت؟
    alternatives_sent = models.BooleanField(default=False)  # اتبعتله مواعيد الرحلات التانية

    class Meta:
        db_table        = 'waitlist_entries'
        unique_together = [('student', 'trip')]
        ordering        = ['-created_at']

    def __str__(self):
        return f"{self.student} — {self.trip} [{self.resolution}]"

    def resolve_refund(self):
        self.resolution  = 'refund'
        self.resolved_at = timezone.now()
        self.save()

    def resolve_credit(self):
        from datetime import timedelta
        self.resolution        = 'credit'
        self.credit_valid_until = self.trip.trip_date + timedelta(weeks=1)
        self.resolved_at       = timezone.now()
        self.save()
        # أنشئ رصيد للطالب
        CreditBalance.objects.update_or_create(
            student=self.student,
            defaults={},
        )
        cb = CreditBalance.objects.get(student=self.student)
        cb.balance       += self.amount_paid
        cb.valid_until    = self.credit_valid_until
        cb.source_entry   = self
        cb.save()


class CreditBalance(models.Model):
    """رصيد مؤقت للطالب — صالح لأسبوع"""
    student      = models.OneToOneField(Student, on_delete=models.CASCADE, related_name='credit_balance')
    balance      = models.DecimalField(max_digits=8, decimal_places=2, default=0)
    valid_until  = models.DateField(null=True, blank=True)
    source_entry = models.ForeignKey(WaitlistEntry, null=True, blank=True,
                                     on_delete=models.SET_NULL, related_name='+')
    created_at   = models.DateTimeField(auto_now_add=True)
    updated_at   = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'credit_balances'

    def __str__(self):
        return f"{self.student} — {self.balance} ج.م (حتى {self.valid_until})"

    @property
    def is_valid(self):
        from datetime import date
        return self.balance > 0 and (not self.valid_until or self.valid_until >= date.today())


class StudentNotification(models.Model):
    """إشعارات داخلية للطلاب"""
    TYPE_CHOICES = [
        ('confirm_reminder', 'تذكير بالتأكيد'),
        ('no_show',          'غياب عن الرحلة'),
        ('alternatives',     'رحلات بديلة'),
        ('refund_initiated', 'استرداد بدأ'),
        ('credit_added',     'رصيد أضيف'),
        ('general',          'عام'),
    ]
    student    = models.ForeignKey(Student, on_delete=models.CASCADE, related_name='notifications')
    type       = models.CharField(max_length=30, choices=TYPE_CHOICES, default='general')
    title_ar   = models.CharField(max_length=200)
    title_en   = models.CharField(max_length=200, blank=True)
    body_ar    = models.TextField()
    body_en    = models.TextField(blank=True)
    is_read    = models.BooleanField(default=False)
    data       = models.JSONField(default=dict, blank=True)   # extra payload
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'student_notifications'
        ordering = ['-created_at']

    def __str__(self):
        return f"[{self.type}] {self.student} — {self.title_ar}"
