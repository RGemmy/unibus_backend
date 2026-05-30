from rest_framework import viewsets, status
from rest_framework.decorators import action, api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from .models import Student, University
from .serializers import StudentSerializer, StudentCreateSerializer, UniversitySerializer


class UniversityViewSet(viewsets.ModelViewSet):
    queryset           = University.objects.all()
    serializer_class   = UniversitySerializer
    permission_classes = [IsAuthenticated]
    search_fields      = ['name']


class StudentViewSet(viewsets.ModelViewSet):
    queryset = (Student.objects
                .select_related('user', 'university')
                .prefetch_related('subscriptions')
                .all())
    permission_classes = [IsAuthenticated]
    search_fields      = ['user__user_name', 'user__email', 'faculty', 'program']
    filterset_fields   = ['university', 'faculty']
    ordering_fields    = ['user__user_name', 'faculty']
    ordering           = ['user__user_name']

    def get_serializer_class(self):
        if self.action == 'create':
            return StudentCreateSerializer
        return StudentSerializer

    def create(self, request, *args, **kwargs):
        serializer = StudentCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        student = serializer.save()
        return Response(StudentSerializer(student).data, status=status.HTTP_201_CREATED)

    @action(detail=False, methods=['get'], url_path='count')
    def count(self, request):
        """Return total student count only — for bus_mod dashboard."""
        return Response({'count': Student.objects.count()})
