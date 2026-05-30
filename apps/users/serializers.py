from rest_framework import serializers
from rest_framework_simplejwt.tokens import RefreshToken
from django.contrib.auth import authenticate
from .models import User, Role, Moderator, Driver


class RoleSerializer(serializers.ModelSerializer):
    class Meta:
        model = Role
        fields = '__all__'


class UserSerializer(serializers.ModelSerializer):
    role_name = serializers.CharField(source='role.name', read_only=True)
    password  = serializers.CharField(write_only=True, required=False)

    class Meta:
        model  = User
        fields = ['id', 'user_name', 'email', 'phone', 'national_id', 'role', 'role_name', 'is_active', 'created_at', 'password']
        read_only_fields = ['created_at']

    def create(self, validated_data):
        password = validated_data.pop('password', None)
        user = User(**validated_data)
        if password:
            user.set_password(password)
        user.save()
        return user

    def update(self, instance, validated_data):
        password = validated_data.pop('password', None)
        for attr, val in validated_data.items():
            setattr(instance, attr, val)
        if password:
            instance.set_password(password)
        instance.save()
        return instance


class RegisterSerializer(serializers.ModelSerializer):
    password  = serializers.CharField(write_only=True, min_length=6)
    password2 = serializers.CharField(write_only=True)

    class Meta:
        model  = User
        fields = ['user_name', 'email', 'password', 'password2', 'phone', 'national_id']

    def validate(self, data):
        if data['password'] != data['password2']:
            raise serializers.ValidationError({'password': 'كلمتا المرور غير متطابقتين'})
        return data

    def create(self, validated_data):
        validated_data.pop('password2')
        password = validated_data.pop('password')
        # Assign student role by default
        student_role, _ = Role.objects.get_or_create(name='student')
        user = User.objects.create_user(password=password, role=student_role, **validated_data)
        return user


class LoginSerializer(serializers.Serializer):
    email    = serializers.EmailField()
    password = serializers.CharField()

    def validate(self, data):
        user = authenticate(email=data['email'], password=data['password'])
        if not user:
            raise serializers.ValidationError('البريد الإلكتروني أو كلمة المرور غير صحيحة')
        if not user.is_active:
            raise serializers.ValidationError('الحساب معطّل')
        data['user'] = user
        return data


class DriverSerializer(serializers.ModelSerializer):
    user_name = serializers.CharField(source='user.user_name', read_only=True)
    email     = serializers.EmailField(source='user.email', read_only=True)
    phone     = serializers.CharField(source='user.phone', read_only=True)
    is_active = serializers.BooleanField(source='user.is_active', read_only=True)

    class Meta:
        model  = Driver
        fields = ['id', 'user', 'user_name', 'email', 'phone', 'is_active',
                  'license_number', 'license_expiry_date',
                  'last_drug_test_date', 'next_drug_test_date']


class ModeratorSerializer(serializers.ModelSerializer):
    user_name = serializers.CharField(source='user.user_name', read_only=True)
    email     = serializers.EmailField(source='user.email', read_only=True)

    class Meta:
        model  = Moderator
        fields = ['id', 'user', 'user_name', 'email', 'affiliation']
