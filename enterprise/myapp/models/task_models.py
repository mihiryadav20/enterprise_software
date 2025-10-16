from django.db import models
from django.conf import settings
from django.utils.translation import gettext_lazy as _
from django.utils import timezone
from .project_models import Project, ProjectMember

class TaskPriority(models.TextChoices):
    LOW = 'low', _('Low')
    MEDIUM = 'medium', _('Medium')
    HIGH = 'high', _('High')
    CRITICAL = 'critical', _('Critical')

class TaskStatus(models.TextChoices):
    TODO = 'todo', _('To Do')
    IN_PROGRESS = 'in_progress', _('In Progress')
    IN_REVIEW = 'in_review', _('In Review')
    DONE = 'done', _('Done')
    BLOCKED = 'blocked', _('Blocked')

class TaskAssignment(models.Model):
    """
    Model representing the assignment of a task to a user.
    """
    task = models.ForeignKey(
        'Task',
        on_delete=models.CASCADE,
        related_name='assignments',
        help_text=_('The task being assigned')
    )
    assignee = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='task_assignments',
        help_text=_('User assigned to the task')
    )
    assigned_at = models.DateTimeField(auto_now_add=True)
    is_lead = models.BooleanField(
        default=False,
        help_text=_('Whether this assignee is the lead for the task')
    )

    class Meta:
        unique_together = ('task', 'assignee')
        verbose_name = _('task assignment')
        verbose_name_plural = _('task assignments')

    def __str__(self):
        return f"{self.assignee.username} assigned to {self.task.title}"

    def save(self, *args, **kwargs):
        # If this is the first assignment, make it the lead
        if not self.pk and not TaskAssignment.objects.filter(task=self.task).exists():
            self.is_lead = True
        super().save(*args, **kwargs)


class Task(models.Model):
    """
    Model representing a task within a project.
    """
    title = models.CharField(
        _('title'),
        max_length=200,
        help_text=_('Short title of the task')
    )
    description = models.TextField(
        _('description'),
        blank=True,
        null=True,
        help_text=_('Detailed description of the task')
    )
    project = models.ForeignKey(
        Project,
        on_delete=models.CASCADE,
        related_name='tasks',
        help_text=_('The project this task belongs to')
    )
    assignees = models.ManyToManyField(
        settings.AUTH_USER_MODEL,
        through='TaskAssignment',
        through_fields=('task', 'assignee'),
        related_name='assigned_tasks',
        help_text=_('Users assigned to this task')
    )
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name='created_tasks',
        help_text=_('User who created this task')
    )
    due_date = models.DateTimeField(
        _('due date'),
        null=True,
        blank=True,
        help_text=_('When this task is due')
    )
    priority = models.CharField(
        _('priority'),
        max_length=10,
        choices=TaskPriority.choices,
        default=TaskPriority.MEDIUM,
        help_text=_('Priority level of the task')
    )
    status = models.CharField(
        _('status'),
        max_length=20,
        choices=TaskStatus.choices,
        default=TaskStatus.TODO,
        help_text=_('Current status of the task')
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    completed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ['-priority', 'due_date']
        verbose_name = _('task')
        verbose_name_plural = _('tasks')
        indexes = [
            models.Index(fields=['project', 'status']),
            models.Index(fields=['due_date']),
        ]

    def __str__(self):
        return f"{self.title} ({self.get_status_display()})"
        
    def get_lead_assignee(self):
        """
        Returns the lead assignee for this task, if any.
        """
        assignment = self.assignments.filter(is_lead=True).first()
        return assignment.assignee if assignment else None

    @property
    def is_overdue(self):
        """
        Returns True if the task is overdue (due date has passed and task is not done).
        """
        if not self.due_date or self.status == TaskStatus.DONE:
            return False
        return timezone.now() > self.due_date

    def save(self, *args, **kwargs):
        # Update completed_at when status changes to DONE
        if self.status == TaskStatus.DONE and not self.completed_at:
            self.completed_at = timezone.now()
        elif self.status != TaskStatus.DONE and self.completed_at:
            self.completed_at = None
        super().save(*args, **kwargs)


class TaskAttachment(models.Model):
    """
    Model for storing file attachments related to tasks.
    """
    task = models.ForeignKey(
        Task,
        on_delete=models.CASCADE,
        related_name='attachments',
        help_text=_('The task this attachment belongs to')
    )
    file = models.FileField(
        _('file'),
        upload_to='task_attachments/%Y/%m/%d/',
        help_text=_('Attached file')
    )
    uploaded_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name='uploaded_task_attachments',
        help_text=_('User who uploaded the file')
    )
    file_name = models.CharField(
        _('file name'),
        max_length=255,
        help_text=_('Original name of the uploaded file')
    )
    file_size = models.PositiveIntegerField(
        _('file size'),
        help_text=_('Size of the file in bytes')
    )
    content_type = models.CharField(
        _('content type'),
        max_length=100,
        help_text=_('MIME type of the file')
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = _('task attachment')
        verbose_name_plural = _('task attachments')
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.file_name} ({self.task.title})"

    def save(self, *args, **kwargs):
        # Set file metadata before saving
        if self.file and not self.pk:
            self.file_name = self.file.name
            self.file_size = self.file.size
            self.content_type = getattr(self.file, 'content_type', '')
        super().save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        """Delete the file from storage when the model is deleted."""
        storage, path = self.file.storage, self.file.path
        super().delete(*args, **kwargs)
        storage.delete(path)
