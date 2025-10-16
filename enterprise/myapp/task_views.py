from rest_framework import viewsets, status, mixins
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.shortcuts import get_object_or_404
from django.db import transaction
from django.contrib.auth import get_user_model

from .models import Task, TaskAttachment, TaskStatus, TaskAssignment
from .task_serializers import TaskSerializer, TaskCreateSerializer, TaskAttachmentSerializer, TaskAssignmentSerializer
from .permissions import IsStaffUser, IsProjectMember, IsTaskAssigneeOrCreator

User = get_user_model()


class TaskViewSet(
    mixins.CreateModelMixin,
    mixins.RetrieveModelMixin,
    mixins.UpdateModelMixin,
    mixins.DestroyModelMixin,
    mixins.ListModelMixin,
    viewsets.GenericViewSet
):
    """
    ViewSet for managing tasks.
    """
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        """
        Return tasks that the user has permission to view.
        """
        queryset = Task.objects.select_related(
            'project', 'created_by'
        ).prefetch_related(
            'attachments',
            'assignments',
            'assignments__assignee'
        )
        
        # Filter by project if project_id is provided
        project_id = self.request.query_params.get('project_id')
        if project_id:
            queryset = queryset.filter(project_id=project_id)
            
        # Filter by assignee if assignee_id is provided
        assignee_id = self.request.query_params.get('assignee_id')
        if assignee_id:
            queryset = queryset.filter(assignments__assignee_id=assignee_id)
            
        # Filter by status if status is provided
        status_param = self.request.query_params.get('status')
        if status_param:
            queryset = queryset.filter(status=status_param)
            
        # Filter by priority if priority is provided
        priority = self.request.query_params.get('priority')
        if priority:
            queryset = queryset.filter(priority=priority)
            
        # Filter by lead assignee if lead_assignee_id is provided
        lead_assignee_id = self.request.query_params.get('lead_assignee_id')
        if lead_assignee_id:
            queryset = queryset.filter(assignments__assignee_id=lead_assignee_id, assignments__is_lead=True)
            
        # Filter by overdue status
        is_overdue = self.request.query_params.get('is_overdue', '').lower()
        if is_overdue == 'true':
            from django.utils import timezone
            queryset = queryset.filter(
                due_date__lt=timezone.now(),
                status__in=[TaskStatus.TODO, TaskStatus.IN_PROGRESS, TaskStatus.IN_REVIEW, TaskStatus.BLOCKED]
            )
        
        # Non-staff users can only see tasks in projects they're members of
        if not self.request.user.is_staff:
            queryset = queryset.filter(
                project__project_members__user=self.request.user
            )
            
        return queryset.distinct()
    
    def get_serializer_class(self):
        """
        Use different serializers for different actions.
        """
        if self.action == 'create':
            return TaskCreateSerializer
        return TaskSerializer
    
    def get_permissions(self):
        """
        Instantiates and returns the list of permissions that this view requires.
        """
        if self.action in ['create']:
            # Only project members can create tasks
            permission_classes = [IsAuthenticated, IsProjectMember]
        elif self.action in ['update', 'partial_update', 'destroy']:
            # Only task creator, assignee, or admin can update/delete
            permission_classes = [IsAuthenticated, IsTaskAssigneeOrCreator | IsStaffUser]
        else:
            # Any authenticated user can view tasks in their projects
            permission_classes = [IsAuthenticated]
            
        return [permission() for permission in permission_classes]
    
    def perform_create(self, serializer):
        """
        Set the created_by field to the current user.
        """
        serializer.save(created_by=self.request.user)
    
    @action(detail=True, methods=['post'], url_path='change-status')
    def change_status(self, request, pk=None):
        """
        Custom action to change task status.
        """
        task = self.get_object()
        new_status = request.data.get('status')
        
        if not new_status:
            return Response(
                {'error': 'Status is required'},
                status=status.HTTP_400_BAD_REQUEST
            )
            
        if new_status not in dict(TaskStatus.choices):
            return Response(
                {'error': 'Invalid status'},
                status=status.HTTP_400_BAD_REQUEST
            )
            
        task.status = new_status
        task.save()
        
        serializer = self.get_serializer(task)
        return Response(serializer.data)
    
    @action(detail=True, methods=['post'], url_path='assign')
    def assign_task(self, request, pk=None):
        """
        Assign a user to a task.
        """
        task = self.get_object()
        user_id = request.data.get('user_id')
        is_lead = request.data.get('is_lead', False)
        
        if not user_id:
            return Response(
                {'error': 'user_id is required'},
                status=status.HTTP_400_BAD_REQUEST
            )
            
        try:
            user = User.objects.get(id=user_id)
        except User.DoesNotExist:
            return Response(
                {'error': 'User not found'},
                status=status.HTTP_404_NOT_FOUND
            )
            
        # Verify the user is a member of the project
        if not task.project.project_members.filter(user=user).exists():
            return Response(
                {'error': 'User is not a member of this project'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Create or update the assignment
        assignment, created = TaskAssignment.objects.update_or_create(
            task=task,
            assignee=user,
            defaults={'is_lead': is_lead}
        )
        
        # If this is the first assignment, make it the lead
        if created and not task.assignments.exists():
            assignment.is_lead = True
            assignment.save()
            
        serializer = self.get_serializer(task)
        return Response(serializer.data)
        
    @action(detail=True, methods=['post'], url_path='unassign')
    def unassign_task(self, request, pk=None):
        """
        Unassign a user from a task.
        """
        task = self.get_object()
        user_id = request.data.get('user_id')
        
        if not user_id:
            return Response(
                {'error': 'user_id is required'},
                status=status.HTTP_400_BAD_REQUEST
            )
            
        try:
            assignment = TaskAssignment.objects.get(task=task, assignee_id=user_id)
            was_lead = assignment.is_lead
            assignment.delete()
            
            # If we removed the lead, assign a new lead if there are other assignees
            if was_lead and task.assignments.exists():
                new_lead = task.assignments.first()
                new_lead.is_lead = True
                new_lead.save()
                
        except TaskAssignment.DoesNotExist:
            return Response(
                {'error': 'User is not assigned to this task'},
                status=status.HTTP_400_BAD_REQUEST
            )
            
        serializer = self.get_serializer(task)
        return Response(serializer.data)
        
    @action(detail=True, methods=['post'], url_path='set-lead')
    def set_lead_assignee(self, request, pk=None):
        """
        Set the lead assignee for a task.
        """
        task = self.get_object()
        user_id = request.data.get('user_id')
        
        if not user_id:
            return Response(
                {'error': 'user_id is required'},
                status=status.HTTP_400_BAD_REQUEST
            )
            
        # Clear existing lead
        task.assignments.update(is_lead=False)
        
        # Set new lead
        try:
            assignment = task.assignments.get(assignee_id=user_id)
            assignment.is_lead = True
            assignment.save()
        except TaskAssignment.DoesNotExist:
            return Response(
                {'error': 'User is not assigned to this task'},
                status=status.HTTP_400_BAD_REQUEST
            )
            
        serializer = self.get_serializer(task)
        return Response(serializer.data)


class TaskAttachmentViewSet(
    mixins.CreateModelMixin,
    mixins.RetrieveModelMixin,
    mixins.DestroyModelMixin,
    mixins.ListModelMixin,
    viewsets.GenericViewSet
):
    """
    ViewSet for managing task attachments.
    """
    serializer_class = TaskAttachmentSerializer
    permission_classes = [IsAuthenticated, IsTaskAssigneeOrCreator | IsStaffUser]
    
    def get_queryset(self):
        """
        Return attachments for the specified task.
        """
        task_id = self.kwargs.get('task_id')
        return TaskAttachment.objects.filter(task_id=task_id)
    
    def perform_create(self, serializer):
        """
        Set the uploaded_by field to the current user and associate with task.
        """
        task_id = self.kwargs.get('task_id')
        task = get_object_or_404(Task, id=task_id)
        serializer.save(
            task=task,
            uploaded_by=self.request.user,
            file_name=self.request.FILES['file'].name,
            file_size=self.request.FILES['file'].size,
            content_type=self.request.FILES['file'].content_type
        )
