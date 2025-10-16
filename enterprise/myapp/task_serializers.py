from rest_framework import serializers
from django.utils.translation import gettext_lazy as _
from .models import Task, TaskAttachment, TaskPriority, TaskStatus
from django.contrib.auth import get_user_model

User = get_user_model()

class TaskAttachmentSerializer(serializers.ModelSerializer):
    """Serializer for task attachments."""
    file = serializers.FileField(use_url=True, required=False)
    file_name = serializers.CharField(read_only=True)
    file_size = serializers.IntegerField(read_only=True)
    content_type = serializers.CharField(read_only=True)
    uploaded_by = serializers.PrimaryKeyRelatedField(
        queryset=User.objects.all(),
        required=False,
        allow_null=True
    )

    class Meta:
        model = TaskAttachment
        fields = [
            'id', 'file', 'file_name', 'file_size', 'content_type',
            'uploaded_by', 'created_at'
        ]
        read_only_fields = ['id', 'created_at']


class TaskSerializer(serializers.ModelSerializer):
    """Serializer for the Task model."""
    priority = serializers.ChoiceField(
        choices=TaskPriority.choices,
        default=TaskPriority.MEDIUM
    )
    status = serializers.ChoiceField(
        choices=TaskStatus.choices,
        default=TaskStatus.TODO
    )
    assignee = serializers.PrimaryKeyRelatedField(
        queryset=User.objects.all(),
        required=False,
        allow_null=True
    )
    assignee_name = serializers.CharField(
        source='assignee.get_full_name',
        read_only=True
    )
    created_by_name = serializers.CharField(
        source='created_by.get_full_name',
        read_only=True
    )
    project_name = serializers.CharField(
        source='project.name',
        read_only=True
    )
    attachments = TaskAttachmentSerializer(many=True, read_only=True)
    attachment_count = serializers.IntegerField(
        source='attachments.count',
        read_only=True
    )
    is_overdue = serializers.SerializerMethodField()

    class Meta:
        model = Task
        fields = [
            'id', 'title', 'description', 'project', 'project_name',
            'assignee', 'assignee_name', 'created_by', 'created_by_name',
            'due_date', 'priority', 'status', 'created_at', 'updated_at',
            'completed_at', 'attachments', 'attachment_count', 'is_overdue'
        ]
        read_only_fields = [
            'id', 'created_at', 'updated_at', 'completed_at',
            'created_by', 'attachments', 'attachment_count', 'is_overdone'
        ]

    def get_is_overdue(self, obj):
        """
        Check if the task is overdue.
        """
        if obj.due_date and obj.status != TaskStatus.DONE:
            from django.utils import timezone
            return timezone.now() > obj.due_date
        return False

    def validate_due_date(self, value):
        """
        Ensure due date is in the future when creating a task.
        """
        if value and value < timezone.now():
            raise serializers.ValidationError("Due date must be in the future.")
        return value

    def create(self, validated_data):
        """
        Create a new task and set the created_by field.
        """
        # Set the created_by field to the current user
        validated_data['created_by'] = self.context['request'].user
        return super().create(validated_data)

    def update(self, instance, validated_data):
        """
        Update a task and handle status changes.
        """
        # Handle status changes
        if 'status' in validated_data:
            new_status = validated_data['status']
            
            # If status is being set to DONE, set completed_at
            if new_status == TaskStatus.DONE and instance.status != TaskStatus.DONE:
                from django.utils import timezone
                instance.completed_at = timezone.now()
            # If status is changed from DONE to something else, clear completed_at
            elif instance.status == TaskStatus.DONE and new_status != TaskStatus.DONE:
                instance.completed_at = None
        
        return super().update(instance, validated_data)


class TaskCreateSerializer(TaskSerializer):
    """
    Specialized serializer for task creation that handles file uploads.
    """
    attachments = serializers.ListField(
        child=serializers.FileField(max_length=100, allow_empty_file=False, use_url=False),
        write_only=True,
        required=False
    )

    class Meta(TaskSerializer.Meta):
        fields = TaskSerializer.Meta.fields + ['attachments']
        read_only_fields = [f for f in TaskSerializer.Meta.read_only_fields 
                          if f != 'created_by']

    def create(self, validated_data):
        """
        Create task and handle file uploads.
        """
        attachments_data = validated_data.pop('attachments', [])
        task = super().create(validated_data)
        
        # Process file uploads
        request = self.context.get('request')
        if request and hasattr(request, 'FILES'):
            for file in request.FILES.getlist('attachments'):
                TaskAttachment.objects.create(
                    task=task,
                    file=file,
                    uploaded_by=request.user,
                    file_name=file.name,
                    file_size=file.size,
                    content_type=file.content_type
                )
        
        return task
