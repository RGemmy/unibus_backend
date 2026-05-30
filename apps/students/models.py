from django.db import models
from apps.users.models import User


class University(models.Model):
    name = models.CharField(max_length=200, unique=True)

    class Meta:
        db_table = 'universities'
        ordering = ['name']

    def __str__(self):
        return self.name


class Student(models.Model):
    LEVEL_CHOICES = [(str(i), f'المستوى {i}') for i in range(1, 9)]

    user       = models.OneToOneField(User, on_delete=models.CASCADE, related_name='student_profile')
    faculty    = models.CharField(max_length=200)
    program    = models.CharField(max_length=200)
    level      = models.CharField(max_length=2, choices=LEVEL_CHOICES, blank=True)
    university = models.ForeignKey(University, on_delete=models.PROTECT, related_name='students')

    class Meta:
        db_table = 'students'

    def __str__(self):
        return f"{self.user.user_name} - {self.university}"
