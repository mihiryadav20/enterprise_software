from django.db import models
from django.conf import settings
from django.utils import timezone
from django.utils.translation import gettext_lazy as _
from django.core.validators import MinValueValidator, MaxValueValidator


class ProjectMember(models.Model):
    """Model to represent project members and their roles."""
    class RoleChoices(models.TextChoices):
        ADMIN = 'admin', _('Admin')
        MEMBER = 'member', _('Member')
        VIEWER = 'viewer', _('Viewer')
    
    project = models.ForeignKey(
        'Project',
        on_delete=models.CASCADE,
        related_name='project_members'
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='project_memberships'
    )
    role = models.CharField(
        max_length=10,
        choices=RoleChoices.choices,
        default=RoleChoices.MEMBER
    )
    joined_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ('project', 'user')
        verbose_name = _('project member')
        verbose_name_plural = _('project members')

    def __str__(self):
        return f"{self.user.username} - {self.get_role_display()} in {self.project.name}"


class Project(models.Model):
    class ProjectStatus(models.TextChoices):
        DRAFT = 'draft', _('Draft')
        PLANNING = 'planning', _('Planning')
        IN_PROGRESS = 'in_progress', _('In Progress')
        ON_HOLD = 'on_hold', _('On Hold')
        COMPLETED = 'completed', _('Completed')
        CANCELLED = 'cancelled', _('Cancelled')
        ARCHIVED = 'archived', _('Archived')

    class ProjectPriority(models.TextChoices):
        LOW = 'low', _('Low')
        MEDIUM = 'medium', _('Medium')
        HIGH = 'high', _('High')
        CRITICAL = 'critical', _('Critical')

    name = models.CharField(
        _('project name'),
        max_length=255,
        help_text=_('The name of the project')
    )
    key = models.CharField(
        _('project key'),
        max_length=10,
        unique=True,
        help_text=_('Short project identifier (e.g., PRJ-001)')
    )
    description = models.TextField(
        _('description'),
        blank=True,
        null=True,
        help_text=_('Detailed description of the project')
    )
    status = models.CharField(
        _('status'),
        max_length=20,
        choices=ProjectStatus.choices,
        default=ProjectStatus.DRAFT,
        help_text=_('Current status of the project')
    )
    priority = models.CharField(
        _('priority'),
        max_length=10,
        choices=ProjectPriority.choices,
        default=ProjectPriority.MEDIUM,
        help_text=_('Priority level of the project')
    )
    start_date = models.DateField(
        _('start date'),
        null=True,
        blank=True,
        help_text=_('Planned start date of the project')
    )
    end_date = models.DateField(
        _('end date'),
        null=True,
        blank=True,
        help_text=_('Planned end date of the project')
    )
    budget = models.DecimalField(
        _('budget'),
        max_digits=15,
        decimal_places=2,
        null=True,
        blank=True,
        help_text=_('Total budget allocated for the project')
    )
    progress = models.PositiveSmallIntegerField(
        _('progress'),
        default=0,
        validators=[MinValueValidator(0), MaxValueValidator(100)],
        help_text=_('Project completion percentage (0-100)')
    )
    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name='owned_projects',
        help_text=_('User who owns the project')
    )
    department = models.ForeignKey(
        'myapp.Department',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='projects',
        help_text=_('Department responsible for the project')
    )
    is_template = models.BooleanField(
        _('is template'),
        default=False,
        help_text=_('Whether this project is a template for new projects')
    )
    is_public = models.BooleanField(
        _('is public'),
        default=False,
        help_text=_('Whether this project is visible to all users')
    )
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name='created_projects',
        help_text=_('User who created the project')
    )
    created_at = models.DateTimeField(_('created at'), auto_now_add=True)
    updated_at = models.DateTimeField(_('updated at'), auto_now=True)
    completed_at = models.DateTimeField(
        _('completed at'),
        null=True,
        blank=True,
        help_text=_('When the project was marked as completed')
    )

    members = models.ManyToManyField(
        settings.AUTH_USER_MODEL,
        through='ProjectMember',
        through_fields=('project', 'user'),
        related_name='projects',
        blank=True
    )

    class Meta:
        verbose_name = _('project')
        verbose_name_plural = _('projects')
        ordering = ['-created_at']
        permissions = [
            ('view_all_projects', 'Can view all projects'),
            ('export_project', 'Can export project data'),
            ('manage_project_members', 'Can add/remove project members'),
        ]

    def __str__(self):
        return f'{self.key} - {self.name}'

    def save(self, *args, **kwargs):
        # Auto-update completed_at when status changes to completed
        if self.status == self.ProjectStatus.COMPLETED and not self.completed_at:
            self.completed_at = timezone.now()
        elif self.status != self.ProjectStatus.COMPLETED and self.completed_at:
            self.completed_at = None
        super().save(*args, **kwargs)

    @property
    def is_active(self):
        return self.status in [
            self.ProjectStatus.PLANNING,
            self.ProjectStatus.IN_PROGRESS
        ]

    @property
    def duration_days(self):
        if self.start_date and self.end_date:
            return (self.end_date - self.start_date).days
        return None
