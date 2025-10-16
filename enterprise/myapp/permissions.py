from rest_framework import permissions
from .models import Project, ProjectMember, Task

class IsOperationsLeadOrStaff(permissions.BasePermission):
    """
    Custom permission to only allow Operations Leads or staff members to create projects.
    """
    message = 'Only Operations Leads and staff members can create projects.'

    def has_permission(self, request, view):
        # Allow all read permissions (GET, HEAD, OPTIONS)
        if request.method in permissions.SAFE_METHODS:
            return True
            
        # Check if user is staff
        if request.user.is_staff:
            return True
            
        # Check if user is an Operations Lead
        if hasattr(request.user, 'profile') and request.user.profile.role:
            return request.user.profile.role.name == 'operations_lead'
            
        return False


class IsStaffUser(permissions.BasePermission):
    """
    Custom permission to only allow staff users to access an endpoint.
    """
    message = 'Only staff users have permission to perform this action.'

    def has_permission(self, request, view):
        return request.user and request.user.is_staff


class IsProjectMember(permissions.BasePermission):
    """
    Custom permission to only allow members of a project to view or create tasks.
    """
    message = 'You must be a member of this project to perform this action.'

    def has_permission(self, request, view):
        # For list/create views, check if project_id is provided and user is a member
        project_id = request.data.get('project') or request.query_params.get('project_id')
        if project_id:
            return ProjectMember.objects.filter(
                project_id=project_id,
                user=request.user
            ).exists()
        return True  # Will be checked in has_object_permission

    def has_object_permission(self, request, view, obj):
        # For retrieve/update/delete, check if user is a member of the project
        if hasattr(obj, 'project'):  # For Task model
            project = obj.project
        else:  # For Project model
            project = obj
            
        return project.project_members.filter(user=request.user).exists()


class IsTaskAssigneeOrCreator(permissions.BasePermission):
    """
    Custom permission to only allow the task assignee or creator to edit it.
    """
    message = 'You must be the task assignee or creator to perform this action.'

    def has_object_permission(self, request, view, obj):
        # Read permissions are allowed to any request,
        # so we'll always allow GET, HEAD or OPTIONS requests.
        if request.method in permissions.SAFE_METHODS:
            return True
            
        # Check if user is the assignee or creator of the task
        return obj.assignee == request.user or obj.created_by == request.user


class CanManageTaskAttachments(permissions.BasePermission):
    """
    Custom permission to only allow task assignee, creator, or project admin to manage attachments.
    """
    message = 'You do not have permission to manage attachments for this task.'

    def has_permission(self, request, view):
        # For create/list views, check if user can access the parent task
        task_id = view.kwargs.get('task_id')
        if task_id:
            try:
                task = Task.objects.get(id=task_id)
                return (
                    task.assignee == request.user or 
                    task.created_by == request.user or
                    task.project.project_members.filter(
                        user=request.user,
                        role=ProjectMember.RoleChoices.ADMIN
                    ).exists()
                )
            except Task.DoesNotExist:
                return False
        return True  # Will be checked in has_object_permission

    def has_object_permission(self, request, view, obj):
        # For retrieve/update/delete, check permissions on the parent task
        task = obj.task
        return (
            task.assignee == request.user or 
            task.created_by == request.user or
            task.project.project_members.filter(
                user=request.user,
                role=ProjectMember.RoleChoices.ADMIN
            ).exists()
        )
