from django.contrib import admin
from .models import WaitlistEntry, CreditBalance, StudentNotification


@admin.register(WaitlistEntry)
class WaitlistEntryAdmin(admin.ModelAdmin):
    list_display  = ['student', 'trip', 'amount_paid', 'resolution', 'alternatives_sent', 'created_at']
    list_filter   = ['resolution', 'alternatives_sent', 'trip__trip_date']
    search_fields = ['student__user__user_name']
    readonly_fields = ['created_at', 'resolved_at', 'credit_valid_until']
    actions       = ['send_alternatives_action']

    @admin.action(description='إرسال مواعيد الرحلات البديلة')
    def send_alternatives_action(self, request, queryset):
        from apps.waitlist.views import WaitlistViewSet
        sent = 0
        for entry in queryset.filter(alternatives_sent=False):
            # استخدم نفس المنطق
            from apps.trips.models import Trip
            from apps.waitlist.models import StudentNotification
            alternatives = Trip.objects.filter(
                trip_date=entry.trip.trip_date, status='active'
            ).exclude(id=entry.trip.id)
            alt_list = [{'id': t.id, 'place': t.place.place_name,
                         'time': str(t.schedule.schedule_time)} for t in alternatives]
            body = (f"غبت عن رحلة {entry.trip.place.place_name}. "
                    + ("رحلات بديلة: " + ", ".join(f"{a['place']} {a['time']}" for a in alt_list)
                       if alt_list else "لا توجد رحلات بديلة."))
            StudentNotification.objects.create(
                student=entry.student, type='alternatives',
                title_ar='رحلات بديلة', body_ar=body, data={'alternatives': alt_list}
            )
            entry.alternatives_sent = True
            entry.save()
            sent += 1
        self.message_user(request, f'تم الإرسال لـ {sent} طالب')


@admin.register(CreditBalance)
class CreditBalanceAdmin(admin.ModelAdmin):
    list_display = ['student', 'balance', 'valid_until', 'is_valid', 'updated_at']
    readonly_fields = ['created_at', 'updated_at']


@admin.register(StudentNotification)
class StudentNotificationAdmin(admin.ModelAdmin):
    list_display  = ['student', 'type', 'title_ar', 'is_read', 'created_at']
    list_filter   = ['type', 'is_read']
    search_fields = ['student__user__user_name', 'title_ar']
