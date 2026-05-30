from django.contrib import admin
from .models import Place, Route, Schedule

@admin.register(Place)
class PlaceAdmin(admin.ModelAdmin):
    list_display  = ['id', 'place_name']
    search_fields = ['place_name']

@admin.register(Route)
class RouteAdmin(admin.ModelAdmin):
    list_display  = ['id', 'start_point', 'end_point']
    search_fields = ['start_point', 'end_point']

@admin.register(Schedule)
class ScheduleAdmin(admin.ModelAdmin):
    list_display  = ['id', 'route', 'schedule_time']
    list_filter   = ['route']
    ordering      = ['schedule_time']
