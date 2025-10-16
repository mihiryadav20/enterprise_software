"""
This module serves as the main package initializer for the myapp Django app.
It provides a clean API for importing models, serializers, and views.
"""

def _import_models():
    """Lazily import models to avoid circular imports."""
    from .models import (
        Department, Role, User, UserProfile,
        Project, ProjectMember, Task, TaskAttachment
    )
    return {
        'Department': Department,
        'Role': Role,
        'User': User,
        'UserProfile': UserProfile,
        'Project': Project,
        'ProjectMember': ProjectMember,
        'Task': Task,
        'TaskAttachment': TaskAttachment,
    }

def _import_serializers():
    """Lazily import serializers."""
    from .serializers import (
        DepartmentSerializer, RoleSerializer, UserProfileSerializer,
        UserSerializer, ProjectMemberSerializer, ProjectSerializer, LoginSerializer
    )
    from .task_serializers import (
        TaskSerializer, TaskCreateSerializer, TaskAttachmentSerializer
    )
    
    return {
        'DepartmentSerializer': DepartmentSerializer,
        'RoleSerializer': RoleSerializer,
        'UserProfileSerializer': UserProfileSerializer,
        'UserSerializer': UserSerializer,
        'ProjectMemberSerializer': ProjectMemberSerializer,
        'ProjectSerializer': ProjectSerializer,
        'LoginSerializer': LoginSerializer,
        'TaskSerializer': TaskSerializer,
        'TaskCreateSerializer': TaskCreateSerializer,
        'TaskAttachmentSerializer': TaskAttachmentSerializer,
    }

def _import_views():
    """Lazily import views."""
    from .views import (
        DepartmentViewSet, RoleViewSet, UserViewSet, UserDetailView,
        ProjectViewSet, LoginView, LogoutView
    )
    from .task_views import TaskViewSet, TaskAttachmentViewSet
    
    return {
        'DepartmentViewSet': DepartmentViewSet,
        'RoleViewSet': RoleViewSet,
        'UserViewSet': UserViewSet,
        'UserDetailView': UserDetailView,
        'ProjectViewSet': ProjectViewSet,
        'LoginView': LoginView,
        'LogoutView': LogoutView,
        'TaskViewSet': TaskViewSet,
        'TaskAttachmentViewSet': TaskAttachmentViewSet,
    }

# Export all the names that should be available when importing from myapp
__all__ = [
    # Models
    'Department', 'Role', 'User', 'UserProfile', 'Project', 'ProjectMember',
    'Task', 'TaskAttachment',
    
    # Serializers
    'DepartmentSerializer', 'RoleSerializer', 'UserProfileSerializer',
    'UserSerializer', 'ProjectMemberSerializer', 'ProjectSerializer', 'LoginSerializer',
    'TaskSerializer', 'TaskCreateSerializer', 'TaskAttachmentSerializer',
    
    # Views
    'DepartmentViewSet', 'RoleViewSet', 'UserViewSet', 'UserDetailView',
    'ProjectViewSet', 'LoginView', 'LogoutView',
    'TaskViewSet', 'TaskAttachmentViewSet'
]

# Use __getattr__ to implement lazy loading of modules
# This prevents circular imports at module level
def __getattr__(name):
    if name in _import_models():
        return _import_models()[name]
    elif name in _import_serializers():
        return _import_serializers()[name]
    elif name in _import_views():
        return _import_views()[name]
    raise AttributeError(f"module 'myapp' has no attribute '{name}'")