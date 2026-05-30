from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import TripViewSet, dashboard_stats

router = DefaultRouter()
router.register('', TripViewSet, basename='trip')

urlpatterns = [
    path('dashboard/stats/', dashboard_stats, name='dashboard-stats'),
    path('', include(router.urls)),
]
