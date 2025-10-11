from rest_framework import viewsets, status, permissions, generics
from rest_framework.decorators import action, api_view, permission_classes
from rest_framework.response import Response
from rest_framework.views import APIView
from django.contrib.auth import get_user_model
from .models import Department, Role, UserProfile
from .serializers import (
    UserSerializer, UserProfileSerializer,
    DepartmentSerializer, RoleSerializer
)
from rest_framework.permissions import IsAuthenticated

User = get_user_model()

class IsOperationsManager(permissions.BasePermission):
    def has_permission(self, request, view):
        return request.user.is_authenticated and hasattr(request.user, 'profile') and \
               request.user.profile.role.name == 'operations_manager'

class UserViewSet(viewsets.ModelViewSet):
    queryset = User.objects.all()
    serializer_class = UserSerializer
    permission_classes = [IsOperationsManager]

    def get_queryset(self):
        # Only return users that the current user has permission to see
        return User.objects.filter(
            profile__department=self.request.user.profile.department
        )

    def perform_create(self, serializer):
        # Set the user who created this record
        serializer.save()

    @action(detail=True, methods=['post'])
    def assign_role(self, request, pk=None):
        user = self.get_object()
        role_id = request.data.get('role_id')
        
        if not role_id:
            return Response(
                {'error': 'role_id is required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            role = Role.objects.get(id=role_id)
            user.profile.role = role
            user.profile.save()
            return Response({'status': 'role assigned'})
        except Role.DoesNotExist:
            return Response(
                {'error': 'Invalid role_id'},
                status=status.HTTP_400_BAD_REQUEST
            )

class DepartmentViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Department.objects.all()
    serializer_class = DepartmentSerializer
    permission_classes = [permissions.IsAuthenticated]

class RoleViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Role.objects.all()
    serializer_class = RoleSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        # Filter roles based on the current user's department if needed
        return Role.objects.all()


class UserProfileView(APIView):
    """
    View to handle user profile operations.
    """
    permission_classes = [IsAuthenticated]
    
    def get(self, request, format=None):
        """
        Retrieve the current user's profile.
        """
        try:
            profile = request.user.profile
            serializer = UserProfileSerializer(profile)
            return Response(serializer.data)
        except UserProfile.DoesNotExist:
            return Response(
                {'error': 'User profile not found'},
                status=status.HTTP_404_NOT_FOUND
            )
    
    def put(self, request, format=None):
        """
        Update the current user's profile.
        """
        try:
            profile = request.user.profile
            serializer = UserProfileSerializer(profile, data=request.data, partial=True)
            if serializer.is_valid():
                serializer.save()
                return Response(serializer.data)
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        except UserProfile.DoesNotExist:
            return Response(
                {'error': 'User profile not found'},
                status=status.HTTP_404_NOT_FOUND
            )
