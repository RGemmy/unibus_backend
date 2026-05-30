from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from .models import User, Role, Driver, Moderator


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    list_display  = ['email', 'user_name', 'role', 'is_active', 'is_staff']
    list_filter   = ['role', 'is_active', 'is_staff']
    search_fields = ['email', 'user_name', 'national_id']
    ordering      = ['-id']
    fieldsets     = (
        (None, {'fields': ('email', 'password')}),
        ('المعلومات الشخصية', {'fields': ('user_name', 'phone', 'national_id', 'role')}),
        ('الصلاحيات', {'fields': ('is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions')}),
    )
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('email', 'user_name', 'password1', 'password2', 'role'),
        }),
    )

admin.site.register(Role)
admin.site.register(Driver)
admin.site.register(Moderator)
