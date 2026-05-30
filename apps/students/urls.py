from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import StudentViewSet, UniversityViewSet

router = DefaultRouter()
router.register('universities', UniversityViewSet, basename='university')
router.register('', StudentViewSet, basename='student')
urlpatterns = [path('', include(router.urls))]
