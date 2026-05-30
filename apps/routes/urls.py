from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import PlaceViewSet, RouteViewSet, ScheduleViewSet

router = DefaultRouter()
router.register('places',    PlaceViewSet,    basename='place')
router.register('schedules', ScheduleViewSet, basename='schedule')
router.register('',          RouteViewSet,    basename='route')
urlpatterns = [path('', include(router.urls))]
