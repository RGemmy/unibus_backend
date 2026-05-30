from django.db import models
from apps.students.models import Student


class Subscription(models.Model):
    STATUS_CHOICES = [('active','فعال'),('cancelled','ملغي'),('expired','منتهي')]
    student    = models.ForeignKey(Student, on_delete=models.CASCADE, related_name='subscriptions')
    status     = models.CharField(max_length=20, choices=STATUS_CHOICES, default='active')
    start_date = models.DateField()
    end_date   = models.DateField()
    plan       = models.CharField(max_length=50, blank=True)
    amount     = models.DecimalField(max_digits=10, decimal_places=2, default=0)

    class Meta:
        db_table = 'subscriptions'
        ordering = ['-start_date']

    def __str__(self):
        return f"{self.student} — {self.plan} ({self.status})"
