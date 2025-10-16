from django.contrib.auth import get_user_model, login, logout
from django.contrib.auth.forms import AuthenticationForm
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt
from rest_framework import viewsets, status, permissions, generics, mixins
from rest_framework.decorators import action, api_view, permission_classes
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated, AllowAny, IsAdminUser
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework.viewsets import GenericViewSet

from .models import Department, Role, UserProfile, Project
from .serializers import (
    UserSerializer, UserProfileSerializer,
    DepartmentSerializer, RoleSerializer, LoginSerializer,
    ProjectSerializer, ProjectMemberSerializer
)
from .permissions import IsOperationsLeadOrStaff

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

        # Get the basic user data
        serializer = UserSerializer(user)
        response_data = serializer.data
        
        # Add phone number to the response
        response_data['phone'] = user.phone
        
        # Add profile information if available
        if hasattr(user, 'profile') and user.profile:
            profile_serializer = UserProfileSerializer(user.profile)
            response_data.update({
                'profile': profile_serializer.data,
                'department': user.profile.department.name if user.profile.department else None,
                'role': user.profile.role.name if user.profile.role else None
            })
        
        return Response(response_data)

class IsStaffUser(permissions.BasePermission):
    """
    Permission check for staff users.
    """
    def has_permission(self, request, view):
        return request.user and request.user.is_staff

class LoginView(APIView):
    """
    API endpoint that allows users to log in and obtain JWT tokens.
    """
    permission_classes = [AllowAny]
    
    @method_decorator(csrf_exempt)
    def dispatch(self, *args, **kwargs):
        return super().dispatch(*args, **kwargs)
    
    def post(self, request, *args, **kwargs):
        serializer = LoginSerializer(
            data=request.data,
            context={'request': request}
        )
        
        if serializer.is_valid():
            user = serializer.validated_data['user']
            
            # Generate JWT tokens
            refresh = RefreshToken.for_user(user)
            
            # Don't use Django's session-based auth
            # login(request, user)  # Commented out to avoid session creation
            
            return Response({
                'refresh': str(refresh),
                'access': str(refresh.access_token),
                'user': {
                    'id': user.id,
                    'username': user.username,
                    'email': user.email,
                    'is_staff': user.is_staff,
                }
            }, status=status.HTTP_200_OK)
            
        return Response(
            {"error": "Invalid credentials"}, 
            status=status.HTTP_400_BAD_REQUEST
        )


class LogoutView(APIView):
    """
    API endpoint that logs out users and blacklists their refresh token.
    """
    authentication_classes = []
    permission_classes = [AllowAny]
    
    @method_decorator(csrf_exempt)
    def dispatch(self, *args, **kwargs):
        return super().dispatch(*args, **kwargs)
    
    def post(self, request, *args, **kwargs):
        try:
            # Accept both "refresh" and "refresh_token" field names
            refresh_token = request.data.get("refresh") or request.data.get("refresh_token")
            if not refresh_token:
                return Response({"error": "Refresh token is required"}, status=status.HTTP_400_BAD_REQUEST)
                
            token = RefreshToken(refresh_token)
            # Use the correct method to blacklist the token
            token.blacklist()
            
            # Clear the session if it exists
            if hasattr(request, 'session'):
                request.session.flush()
                
            return Response(
                {"message": "Successfully logged out."}, 
                status=status.HTTP_205_RESET_CONTENT
            )
        except AttributeError:
            # If blacklist() method doesn't exist, try the alternative
            try:
                from rest_framework_simplejwt.token_blacklist.models import BlacklistedToken, OutstandingToken
                token = RefreshToken(refresh_token)
                jti = token['jti']
                outstanding_token = OutstandingToken.objects.get(jti=jti)
                BlacklistedToken.objects.get_or_create(token=outstanding_token)
                
                return Response(
                    {"message": "Successfully logged out."}, 
                    status=status.HTTP_205_RESET_CONTENT
                )
            except Exception as e:
                return Response(
                    {"error": f"Failed to blacklist token: {str(e)}"}, 
                    status=status.HTTP_400_BAD_REQUEST
                )
        except Exception as e:
            return Response(
                {"error": f"Invalid token or token is expired: {str(e)}"}, 
                status=status.HTTP_400_BAD_REQUEST
            )


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
        user = serializer.save()
        # Set a default password if not provided
        if not user.password:
            user.set_password('defaultpassword')
            user.save()

    @action(detail=True, methods=['post'])
    def assign_role(self, request, pk=None):
        user = self.get_object()
        role_id = request.data.get('role_id')
        try:
            role = Role.objects.get(pk=role_id)
            profile, created = UserProfile.objects.get_or_create(user=user)
            profile.role = role
            profile.save()
            return Response({'status': 'role assigned'})
        except Role.DoesNotExist:
            return Response(
                {'error': 'Role not found'},
                status=status.HTTP_400_BAD_REQUEST
            )


class ProjectViewSet(mixins.CreateModelMixin,
                    mixins.RetrieveModelMixin,
                    mixins.ListModelMixin,
                    GenericViewSet):
    """
    API endpoint that allows projects to be created and viewed.
    """
    queryset = Project.objects.all()
    serializer_class = ProjectSerializer
    permission_classes = [IsAuthenticated, IsOperationsLeadOrStaff]

    def get_serializer_context(self):
        """
        Extra context provided to the serializer class.
        """
        return {
            'request': self.request,
            'format': self.format_kwarg,
            'view': self
        }

    def perform_create(self, serializer):
        """
        Set the created_by field to the current user.
        """
        serializer.save(created_by=self.request.user)

    def get_queryset(self):
        """
        Filter projects based on user permissions.
        """
        user = self.request.user
        
        # Staff and Operations Leads can see all projects
        if user.is_staff or (hasattr(user, 'profile') and 
                           user.profile.role and 
                           user.profile.role.name == 'operations_lead'):
            return Project.objects.all()
            
        # Regular users can only see projects they're members of
        return Project.objects.filter(members=user)

    @action(detail=True, methods=['post'], url_path='add-members')
    def add_members(self, request, pk=None):
        """
        Add members to a project.
        Only project admins can add members.
        """
        project = self.get_object()
        
        # Check if user is admin of the project
        if not project.members.through.objects.filter(
            user=request.user, 
            project=project,
            role='admin'
        ).exists() and not request.user.is_staff:
            return Response(
                {'error': 'You do not have permission to add members to this project'},
                status=status.HTTP_403_FORBIDDEN
            )
            
        serializer = ProjectMemberSerializer(data=request.data, many=True)
        if serializer.is_valid():
            members_data = serializer.validated_data
            
            with transaction.atomic():
                for member_data in members_data:
                    project.members.add(
                        member_data['user'],
                        through_defaults={'role': member_data['role']}
                    )
            
            return Response(
                {'status': 'Members added successfully'},
                status=status.HTTP_201_CREATED
            )
            
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


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
