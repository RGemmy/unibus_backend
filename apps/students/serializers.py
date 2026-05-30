from rest_framework import serializers
from .models import Student, University


class UniversitySerializer(serializers.ModelSerializer):
    student_count = serializers.IntegerField(source='students.count', read_only=True)
    class Meta:
        model  = University
        fields = ['id', 'name', 'student_count']


class StudentSerializer(serializers.ModelSerializer):
    user_name        = serializers.CharField(source='user.user_name',    read_only=True)
    email            = serializers.EmailField(source='user.email',       read_only=True)
    phone            = serializers.CharField(source='user.phone',        read_only=True)
    national_id      = serializers.CharField(source='user.national_id',  read_only=True)
    is_active        = serializers.BooleanField(source='user.is_active', read_only=True)
    university_name  = serializers.CharField(source='university.name',   read_only=True)
    has_subscription = serializers.SerializerMethodField()

    class Meta:
        model  = Student
        fields = [
            'id', 'user', 'user_name', 'email', 'phone', 'national_id',
            'is_active', 'faculty', 'program', 'level',
            'university', 'university_name', 'has_subscription',
        ]

    def get_has_subscription(self, obj):
        return obj.subscriptions.filter(status='active').exists()


class StudentCreateSerializer(serializers.Serializer):
    """Create User + Student in one request."""
    from apps.users.models import User
    user_name   = serializers.CharField()
    email       = serializers.EmailField()
    password    = serializers.CharField(write_only=True, min_length=6)
    phone       = serializers.CharField(required=False, allow_blank=True)
    national_id = serializers.CharField(required=False, allow_blank=True)
    faculty     = serializers.CharField(required=False, allow_blank=True)
    program     = serializers.CharField(required=False, allow_blank=True)
    level       = serializers.CharField(required=False, allow_blank=True)
    university  = serializers.PrimaryKeyRelatedField(
        queryset=University.objects.all(), required=False, allow_null=True)

    def create(self, validated_data):
        from apps.users.models import User, Role
        role, _ = Role.objects.get_or_create(name='student')
        user = User.objects.create_user(
            email=validated_data['email'],
            password=validated_data['password'],
            user_name=validated_data['user_name'],
            phone=validated_data.get('phone', ''),
            national_id=validated_data.get('national_id', ''),
            role=role,
        )
        student = Student.objects.create(
            user=user,
            faculty=validated_data.get('faculty', ''),
            program=validated_data.get('program', ''),
            level=validated_data.get('level', ''),
            university=validated_data.get('university'),
        )
        return student
