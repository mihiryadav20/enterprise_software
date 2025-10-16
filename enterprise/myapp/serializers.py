from rest_framework import serializers
from django.contrib.auth import get_user_model, authenticate
from django.contrib.auth.forms import AuthenticationForm
from django.utils.translation import gettext_lazy as _
from .models import Department, Role, UserProfile, Project, ProjectMember
from django.db import transaction

User = get_user_model()

class DepartmentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Department
        fields = ['id', 'name', 'description']

class RoleSerializer(serializers.ModelSerializer):
    class Meta:
        model = Role
        fields = ['id', 'name', 'description']

class UserProfileSerializer(serializers.ModelSerializer):
    department = DepartmentSerializer(read_only=True)
    department_id = serializers.PrimaryKeyRelatedField(
        queryset=Department.objects.all(),
        source='department',
        write_only=True,
        required=False,
        allow_null=True
    )
    role = RoleSerializer(read_only=True)
    role_id = serializers.PrimaryKeyRelatedField(
        queryset=Role.objects.all(),
        source='role',
        write_only=True,
        required=False,
        allow_null=True
    )
    
    class Meta:
        model = UserProfile
        fields = [
            'id', 'user', 'department', 'department_id', 
            'role', 'role_id', 'bio', 'date_of_birth',
            'address', 'city', 'country', 'postal_code'
        ]
        read_only_fields = ['user']

class UserSerializer(serializers.ModelSerializer):
    profile = UserProfileSerializer(required=False)
    password = serializers.CharField(write_only=True, required=True, style={'input_type': 'password'})
    
    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'first_name', 'last_name', 'password', 'profile']
        extra_kwargs = {
            'email': {'required': True},
            'first_name': {'required': True},
            'last_name': {'required': True},
        }
    
    def create(self, validated_data):
        profile_data = validated_data.pop('profile', {})
        password = validated_data.pop('password')
        user = User(**validated_data)
        user.set_password(password)
        user.save()
        
        # Create or update profile
        profile_serializer = UserProfileSerializer(
            instance=user.profile if hasattr(user, 'profile') else None,
            data=profile_data,
            partial=True
        )
        if profile_serializer.is_valid():
            profile_serializer.save(user=user)
        return user


class ProjectMemberSerializer(serializers.ModelSerializer):
    """Serializer for project members."""
    user_id = serializers.PrimaryKeyRelatedField(
        queryset=User.objects.all(),
        source='user'
    )
    username = serializers.CharField(source='user.username', read_only=True)

    class Meta:
        model = ProjectMember
        fields = ['user_id', 'username', 'role']


class ProjectSerializer(serializers.ModelSerializer):
    """Serializer for Project model with member management."""
    members = ProjectMemberSerializer(many=True, required=False, source='project_members')
    owner_id = serializers.PrimaryKeyRelatedField(
        queryset=User.objects.all(),
        source='owner',
        required=True
    )
    department_id = serializers.PrimaryKeyRelatedField(
        queryset=Department.objects.all(),
        source='department',
        required=False,
        allow_null=True
    )

    class Meta:
        model = Project
        fields = [
            'id', 'key', 'name', 'description', 'status', 'priority',
            'start_date', 'end_date', 'budget', 'progress', 'owner_id',
            'department_id', 'is_template', 'is_public', 'members', 'created_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at', 'completed_at']

    def validate_key(self, value):
        """Validate project key format (e.g., PRJ-001)."""
        if not value.startswith('PRJ-'):
            raise serializers.ValidationError("Project key must start with 'PRJ-'")
        return value

    def create(self, validated_data):
        """Create project with members."""
        members_data = validated_data.pop('project_members', [])
        
        with transaction.atomic():
            # Create the project
            project = Project.objects.create(**validated_data)
            
            # Add members if provided
            for member_data in members_data:
                project.members.add(
                    member_data['user'],
                    through_defaults={'role': member_data['role']}
                )
            
            # Add creator as admin if not already in members
            creator = self.context['request'].user
            if not any(m['user'] == creator for m in members_data):
                project.members.add(
                    creator,
                    through_defaults={'role': 'admin'}
                )
            
            return project


class LoginSerializer(serializers.Serializer):
    """
    Serializer for user authentication.
    """
    username = serializers.CharField(
        label=_("Username"),
        write_only=True
    )
    password = serializers.CharField(
        label=_("Password"),
        style={'input_type': 'password'},
        trim_whitespace=False,
        write_only=True
    )
    token = serializers.CharField(
        label=_("Token"),
        read_only=True
    )

    def validate(self, attrs):
        username = attrs.get('username')
        password = attrs.get('password')

        if username and password:
            user = authenticate(
                request=self.context.get('request'),
                username=username,
                password=password
            )

            if not user:
                msg = _('Unable to log in with provided credentials.')
                raise serializers.ValidationError(msg, code='authorization')
            
            if not user.is_active:
                msg = _('User account is disabled.')
                raise serializers.ValidationError(msg, code='authorization')

        else:
            msg = _('Must include "username" and "password".')
            raise serializers.ValidationError(msg, code='authorization')

        attrs['user'] = user
        return attrs
