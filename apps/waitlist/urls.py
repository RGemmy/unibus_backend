from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import WaitlistViewSet, StudentNotificationViewSet, CreditBalanceViewSet

router = DefaultRouter()
router.register('entries',        WaitlistViewSet,              basename='waitlist')
router.register('notifications',  StudentNotificationViewSet,   basename='notification')
router.register('credits',        CreditBalanceViewSet,         basename='credit')

urlpatterns = [path('', include(router.urls))]
