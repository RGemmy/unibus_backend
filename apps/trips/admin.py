from django.contrib import admin
from .models import Trip

@admin.register(Trip)
class TripAdmin(admin.ModelAdmin):
    list_display  = ['id', 'place', 'bus', 'trip_date', 'status', 'reserved_seats']
    list_filter   = ['status', 'trip_date']
    search_fields = ['place__place_name', 'bus__plate_number']
    ordering      = ['-trip_date']
