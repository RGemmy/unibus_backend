from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import TripReservationViewSet

router = DefaultRouter()
router.register('', TripReservationViewSet, basename='reservation')
urlpatterns = [path('', include(router.urls))]
