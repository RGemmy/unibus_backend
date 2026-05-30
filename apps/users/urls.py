from django.urls import path, include
from rest_framework.routers import DefaultRouter
from rest_framework_simplejwt.views import TokenRefreshView
from . import views

router = DefaultRouter()
router.register('users',      views.UserViewSet,      basename='user')
router.register('roles',      views.RoleViewSet,      basename='role')
router.register('drivers',    views.DriverViewSet,    basename='driver')
router.register('moderators', views.ModeratorViewSet, basename='moderator')

urlpatterns = [
    path('register/', views.RegisterView.as_view(), name='register'),
    path('login/',    views.LoginView.as_view(),    name='login'),
    path('logout/',   views.logout_view,            name='logout'),
    path('me/',       views.me_view,                name='me'),
    path('token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('', include(router.urls)),
]

# Dashboard
from .dashboard import dashboard_stats
urlpatterns += [
    path('dashboard/stats/', dashboard_stats, name='dashboard-stats'),
]
