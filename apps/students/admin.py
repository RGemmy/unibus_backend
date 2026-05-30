from django.contrib import admin
from .models import Student, University

@admin.register(Student)
class StudentAdmin(admin.ModelAdmin):
    list_display  = ['user', 'faculty', 'program', 'university']
    list_filter   = ['university', 'faculty']
    search_fields = ['user__user_name', 'user__email']

admin.site.register(University)
