from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin
from django.db import models


class Role(models.Model):
    name = models.CharField(max_length=50, unique=True)

    class Meta:
        db_table = 'roles'

    def __str__(self):
        return self.name


class UserManager(BaseUserManager):
    def create_user(self, email, password=None, **extra):
        if not email:
            raise ValueError('Email is required')
        email = self.normalize_email(email)
        user = self.model(email=email, **extra)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password=None, **extra):
        extra.setdefault('is_staff', True)
        extra.setdefault('is_superuser', True)
        return self.create_user(email, password, **extra)


class User(AbstractBaseUser, PermissionsMixin):
    user_name   = models.CharField(max_length=150)
    email       = models.EmailField(unique=True)
    phone       = models.CharField(max_length=20, blank=True)
    national_id = models.CharField(max_length=20, blank=True)
    role        = models.ForeignKey(Role, null=True, blank=True, on_delete=models.SET_NULL)
    is_active   = models.BooleanField(default=True)
    is_staff    = models.BooleanField(default=False)
    created_at  = models.DateTimeField(auto_now_add=True)

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['user_name']

    objects = UserManager()

    class Meta:
        db_table = 'users'

    def __str__(self):
        return self.email


class Moderator(models.Model):
    user        = models.OneToOneField(User, on_delete=models.CASCADE, related_name='moderator_profile')
    affiliation = models.CharField(max_length=200, blank=True)

    class Meta:
        db_table = 'moderators'

    def __str__(self):
        return f"Moderator: {self.user.user_name}"


class Driver(models.Model):
    user                = models.OneToOneField(User, on_delete=models.CASCADE, related_name='driver_profile')
    license_number      = models.CharField(max_length=50, unique=True)
    license_expiry_date = models.DateField()
    last_drug_test_date = models.DateField(null=True, blank=True)
    next_drug_test_date = models.DateField(null=True, blank=True)

    class Meta:
        db_table = 'drivers'

    def __str__(self):
        return f"Driver: {self.user.user_name}"
