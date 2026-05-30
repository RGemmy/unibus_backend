from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import PaymentViewSet, PaymentTypeViewSet

router = DefaultRouter()
router.register('types', PaymentTypeViewSet, basename='payment-type')
router.register('',      PaymentViewSet,     basename='payment')
urlpatterns = [path('', include(router.urls))]
