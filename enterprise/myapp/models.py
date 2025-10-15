from django.db import models
from django.conf import settings
from django.contrib.auth.models import AbstractUser, Group, Permission
from django.utils import timezone
from django.utils.translation import gettext_lazy as _
from django.core.validators import MinValueValidator, MaxValueValidator

class Department(models.Model):
    name = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Department'
        verbose_name_plural = 'Departments'
        ordering = ['name']

    def __str__(self):
        return self.name

class Role(models.Model):
    ROLE_CHOICES = [
        ('operations_manager', 'Operations Manager'),
        ('operations_lead', 'Operations Lead'),
        ('operations_specialist', 'Operations Specialist'),
        ('viewer', 'Viewer'),
        ('stakeholder', 'Stakeholder'),
    ]
    
    name = models.CharField(max_length=50, choices=ROLE_CHOICES, unique=True)
    description = models.TextField(blank=True, null=True)
    permissions = models.ManyToManyField(
        Permission,
        verbose_name=_('permissions'),
        blank=True,
        related_name='role_permissions'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Role'
        verbose_name_plural = 'Roles'
        ordering = ['name']

    def __str__(self):
        return self.get_name_display()

class User(AbstractUser):
    email = models.EmailField(_('email address'), unique=True)
    phone = models.CharField(max_length=20, blank=True, null=True)
    is_verified = models.BooleanField(default=False)
    last_login_ip = models.GenericIPAddressField(blank=True, null=True)
    
    # Remove the default groups and user_permissions from AbstractUser
    groups = None
    user_permissions = None
    
    class Meta(AbstractUser.Meta):
        swappable = 'AUTH_USER_MODEL'
        verbose_name = 'User'
        verbose_name_plural = 'Users'

class UserProfile(models.Model):
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='profile'
    )
    department = models.ForeignKey(
        Department, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True,
        related_name='members'
    )
    role = models.ForeignKey(
        Role,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='users'
    )
    bio = models.TextField(blank=True, null=True)
    date_of_birth = models.DateField(blank=True, null=True)
    address = models.TextField(blank=True, null=True)
    city = models.CharField(max_length=100, blank=True, null=True)
    country = models.CharField(max_length=100, blank=True, null=True)
    postal_code = models.CharField(max_length=20, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'User Profile'
        verbose_name_plural = 'User Profiles'
        ordering = ['user__last_name', 'user__first_name']

    def __str__(self):
        return f'{self.user.username} - {self.department}'


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
        'Department',
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