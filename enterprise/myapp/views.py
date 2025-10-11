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

class UserDetailView(APIView):
    """
    View to retrieve user details.
    Users can view their own details, admins can view any user's details.
    """
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, username=None):
        # If no username is provided, return the current user's details
        if username is None or username.lower() == 'me':
            user = request.user
        else:
            # Check if the requesting user is an admin
            if not (request.user.is_staff or request.user.is_superuser):
                return Response(
                    {"detail": "You do not have permission to view this user's details."},
                    status=status.HTTP_403_FORBIDDEN
                )
            try:
                user = User.objects.get(username=username)
            except User.DoesNotExist:
                return Response(
                    {"detail": "User not found."},
                    status=status.HTTP_404_NOT_FOUND
                )

        # Check if the requesting user has permission to view this user's details
        if not (request.user.is_staff or request.user.is_superuser or request.user == user):
            return Response(
                {"detail": "You do not have permission to view this user's details."},
                status=status.HTTP_403_FORBIDDEN
            )

        serializer = UserSerializer(user)
        return Response(serializer.data)

class IsStaffUser(permissions.BasePermission):
    """
    Permission check for staff users.
    """
    def has_permission(self, request, view):
        return request.user and request.user.is_staff

class UserViewSet(viewsets.ModelViewSet):
    """
    API endpoint that allows users to be viewed or edited.
    Only accessible to staff users.
    """
    queryset = User.objects.all()
    serializer_class = UserSerializer
    permission_classes = [IsStaffUser]

    def get_queryset(self):
        # For staff users, return all users
        if self.request.user.is_staff:
            return User.objects.all()
            
        # For non-staff users, return users in the same department
        # Only if the current user has a profile with a department
        if hasattr(self.request.user, 'profile') and self.request.user.profile.department:
            return User.objects.filter(
                profile__department=self.request.user.profile.department
            )
            
        # If the current user doesn't have a profile or department,
        # return an empty queryset (they can only see themselves)
        return User.objects.filter(id=self.request.user.id)

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

class DepartmentViewSet(viewsets.ModelViewSet):
    """
    API endpoint that allows departments to be viewed or edited.
    Only accessible to staff users.
    """
    queryset = Department.objects.all()
    serializer_class = DepartmentSerializer
    permission_classes = [IsStaffUser]

class RoleViewSet(viewsets.ModelViewSet):
    """
    API endpoint that allows roles to be viewed or edited.
    Only accessible to staff users.
    """
    queryset = Role.objects.all()
    serializer_class = RoleSerializer
    permission_classes = [IsStaffUser]

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
