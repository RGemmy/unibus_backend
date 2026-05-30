from django.contrib import admin
from .models import Payment, PaymentType

admin.site.register(PaymentType)

@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display = ['id', 'trip_reservation', 'amount', 'status', 'created_at']
    list_filter  = ['status', 'payment_type']
