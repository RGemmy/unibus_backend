from django.db import models
from apps.buses.models import Bus
from apps.routes.models import Place, Schedule


class Trip(models.Model):
    STATUS_CHOICES = [
        ('pending',   'قيد الانتظار'),
        ('active',    'نشطة'),
        ('completed', 'مكتملة'),
        ('cancelled', 'ملغية'),
    ]

    place      = models.ForeignKey(Place,    on_delete=models.PROTECT, related_name='trips')
    bus        = models.ForeignKey(Bus,      on_delete=models.PROTECT, related_name='trips')
    schedule   = models.ForeignKey(Schedule, on_delete=models.PROTECT, related_name='trips')
    trip_date  = models.DateField()
    status     = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    end_time   = models.TimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'trips'
        ordering = ['-trip_date', 'schedule__schedule_time']

    def __str__(self):
        return f"Trip to {self.place} on {self.trip_date}"

    @property
    def reserved_seats(self):
        return self.reservations.filter(status__in=['confirmed', 'pending']).count()

    @property
    def available_seats(self):
        return self.bus.capacity - self.reserved_seats
