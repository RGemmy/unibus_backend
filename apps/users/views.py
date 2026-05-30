from rest_framework import generics, status, viewsets
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated, AllowAny, IsAdminUser
from rest_framework.response import Response
from rest_framework_simplejwt.tokens import RefreshToken
from .models import User, Role, Driver, Moderator
from .serializers import (
    UserSerializer, RegisterSerializer, LoginSerializer,
    RoleSerializer, DriverSerializer, ModeratorSerializer
)


# ─── Auth ────────────────────────────────────────────────
class RegisterView(generics.CreateAPIView):
    serializer_class   = RegisterSerializer
    permission_classes = [AllowAny]

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        refresh = RefreshToken.for_user(user)
        return Response({
            'token': str(refresh.access_token),
            'refresh': str(refresh),
            'user': UserSerializer(user).data,
        }, status=status.HTTP_201_CREATED)


class LoginView(generics.GenericAPIView):
    serializer_class   = LoginSerializer
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.validated_data['user']
        refresh = RefreshToken.for_user(user)
        return Response({
            'token': str(refresh.access_token),
            'refresh': str(refresh),
            'user': UserSerializer(user).data,
        })


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def logout_view(request):
    try:
        token = RefreshToken(request.data.get('refresh'))
        token.blacklist()
    except Exception:
        pass
    return Response({'detail': 'تم تسجيل الخروج'})


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def me_view(request):
    return Response(UserSerializer(request.user).data)


# ─── Users CRUD ──────────────────────────────────────────
class UserViewSet(viewsets.ModelViewSet):
    queryset           = User.objects.all().select_related('role')
    serializer_class   = UserSerializer
    permission_classes = [IsAuthenticated]
    search_fields      = ['user_name', 'email', 'phone', 'national_id']
    filterset_fields   = ['role', 'is_active']
    ordering_fields    = ['created_at', 'user_name']
    ordering           = ['-created_at']


# ─── Roles ───────────────────────────────────────────────
class RoleViewSet(viewsets.ModelViewSet):
    queryset           = Role.objects.all()
    serializer_class   = RoleSerializer
    permission_classes = [IsAuthenticated]


# ─── Drivers ─────────────────────────────────────────────
class DriverViewSet(viewsets.ModelViewSet):
    queryset           = Driver.objects.all().select_related('user')
    serializer_class   = DriverSerializer
    permission_classes = [IsAuthenticated]
    search_fields      = ['user__user_name', 'license_number']
    ordering           = ['user__user_name']


# ─── Moderators ──────────────────────────────────────────
class ModeratorViewSet(viewsets.ModelViewSet):
    queryset           = Moderator.objects.all().select_related('user')
    serializer_class   = ModeratorSerializer
    permission_classes = [IsAuthenticated]
