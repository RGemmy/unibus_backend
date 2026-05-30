from django.contrib import admin
from .models import TripReservation

@admin.register(TripReservation)
class TripReservationAdmin(admin.ModelAdmin):
    list_display  = ['student', 'trip', 'status', 'trip_reservation_date']
    list_filter   = ['status']
    search_fields = ['student__user__user_name']
