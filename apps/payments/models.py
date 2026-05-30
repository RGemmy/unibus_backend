from django.db import models
from apps.reservations.models import TripReservation


class PaymentType(models.Model):
    payment_type_name = models.CharField(max_length=100, unique=True)
    class Meta:
        db_table = 'payment_types'
    def __str__(self): return self.payment_type_name


class Payment(models.Model):
    STATUS_CHOICES = [('paid','مدفوع'),('pending','معلق'),('failed','فاشل')]
    trip_reservation = models.OneToOneField(TripReservation, on_delete=models.CASCADE, related_name='payment')
    payment_type     = models.ForeignKey(PaymentType, on_delete=models.SET_NULL, null=True)
    amount           = models.DecimalField(max_digits=10, decimal_places=2)
    status           = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    paid_at          = models.DateTimeField(null=True, blank=True)
    created_at       = models.DateTimeField(auto_now_add=True)
    class Meta:
        db_table = 'payments'
        ordering = ['-created_at']
    def __str__(self): return f"Payment #{self.id} — {self.amount}"
