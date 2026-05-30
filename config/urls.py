from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/auth/',          include('apps.users.urls')),
    path('api/buses/',         include('apps.buses.urls')),
    path('api/routes/',        include('apps.routes.urls')),
    path('api/trips/',         include('apps.trips.urls')),
    path('api/students/',      include('apps.students.urls')),
    path('api/reservations/',  include('apps.reservations.urls')),
    path('api/payments/',      include('apps.payments.urls')),
    path('api/subscriptions/', include('apps.subscriptions.urls')),
    path('api/waitlist/',      include('apps.waitlist.urls')),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

# Dashboard stats shortcut
from apps.trips.views import dashboard_stats
urlpatterns += [path('api/dashboard/stats/', dashboard_stats, name='dashboard-stats')]
