# Import all models to make them available at myapp.models
from .user_models import Department, Role, User, UserProfile
from .project_models import Project, ProjectMember
from .task_models import Task, TaskAttachment, TaskPriority, TaskStatus

# Make models available at package level
__all__ = [
    'Department',
    'Role',
    'User',
    'UserProfile',
    'Project',
    'ProjectMember',
    'Task',
    'TaskAttachment',
    'TaskPriority',
    'TaskStatus',
]
