from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.contrib.auth.forms import UserChangeForm, UserCreationForm
from django.utils.translation import gettext_lazy as _
from django.utils.html import format_html
from django.urls import reverse
from .models import (
    Department, Project, User, UserProfile, Role, 
    Task, TaskAttachment, TaskStatus, TaskPriority, TaskAssignment
)
from django.utils import timezone

# Inline for UserProfile
class UserProfileInline(admin.StackedInline):
    model = UserProfile
    can_delete = False
    verbose_name_plural = 'Profile'
    fk_name = 'user'
    extra = 0

class CustomUserAdmin(UserAdmin):
    form = UserChangeForm
    add_form = UserCreationForm
    inlines = (UserProfileInline,)
    list_display = ('username', 'email', 'first_name', 'last_name', 'is_staff', 'is_verified')
    list_filter = ('is_staff', 'is_superuser', 'is_active', 'is_verified')
    fieldsets = (
        (None, {'fields': ('username', 'password')}),
        (_('Personal info'), {'fields': ('first_name', 'last_name', 'email', 'phone')}),
        (_('Permissions'), {
            'fields': ('is_active', 'is_staff', 'is_superuser', 'is_verified'),
        }),
        (_('Important dates'), {'fields': ('last_login', 'date_joined')}),
    )
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('username', 'email', 'password1', 'password2'),
        }),
    )
    search_fields = ('username', 'first_name', 'last_name', 'email')
    ordering = ('username',)
    filter_horizontal = ()

    def get_inline_instances(self, request, obj=None):
        if not obj:
            return []
        return super().get_inline_instances(request, obj)

class TaskAttachmentInline(admin.TabularInline):
    model = TaskAttachment
    extra = 0
    readonly_fields = ('file_size', 'created_at', 'content_type_display')
    fields = ('file', 'file_name', 'file_size', 'content_type_display', 'created_at')
    
    def has_add_permission(self, request, obj=None):
        return True
        
    def content_type_display(self, obj):
        return obj.content_type
    content_type_display.short_description = 'Content Type'

class TaskAssignmentInline(admin.TabularInline):
    model = TaskAssignment
    extra = 1
    autocomplete_fields = ['assignee']
    verbose_name = 'Assignment'
    verbose_name_plural = 'Assignments'

class TaskAdmin(admin.ModelAdmin):
    list_display = ('title', 'project', 'display_assignees', 'status', 'priority', 'due_date', 'is_overdue_display', 'created_by', 'created_at')
    list_filter = ('status', 'priority', 'project', 'assignments__assignee', 'created_at')
    search_fields = ('title', 'description', 'project__name', 'assignments__assignee__username')
    readonly_fields = ('created_at', 'updated_at', 'completed_at', 'is_overdue_display', 'display_assignees')
    list_editable = ('status', 'priority')
    date_hierarchy = 'due_date'
    inlines = [TaskAssignmentInline, TaskAttachmentInline]
    
    fieldsets = (
        (None, {
            'fields': ('title', 'description', 'project')
        }),
        ('Status & Priority', {
            'fields': ('status', 'priority', 'due_date', 'is_overdue_display')
        }),
        ('Assignments', {
            'classes': ('collapse',),
            'fields': ('display_assignees',)
        }),
        ('Timestamps', {
            'classes': ('collapse',),
            'fields': ('created_at', 'updated_at', 'completed_at', 'created_by')
        }),
    )
    
    def display_assignees(self, obj):
        return ", ".join([f"{a.assignee.get_full_name() or a.assignee.username} (Lead)" if a.is_lead else 
                         a.assignee.get_full_name() or a.assignee.username 
                         for a in obj.assignments.all()])
    display_assignees.short_description = 'Assignees'
    
    def is_overdue_display(self, obj):
        return obj.is_overdue
    is_overdue_display.boolean = True
    is_overdue_display.short_description = 'Is Overdue'
    
    def get_queryset(self, request):
        return super().get_queryset(request).prefetch_related('assignments__assignee')
    
    def save_model(self, request, obj, form, change):
        if not obj.pk:  # Only set created_by during the first save
            obj.created_by = request.user
        super().save_model(request, obj, form, change)
        
        # Ensure at least one lead assignee
        if obj.assignments.exists() and not obj.assignments.filter(is_lead=True).exists():
            first_assignment = obj.assignments.first()
            first_assignment.is_lead = True
            first_assignment.save()

class TaskAttachmentAdmin(admin.ModelAdmin):
    list_display = ('file_name', 'task_link', 'file_size', 'content_type_display', 'uploaded_by', 'created_at')
    list_filter = ('content_type', 'created_at')
    search_fields = ('file_name', 'task__title')
    readonly_fields = ('file_size', 'created_at', 'content_type_display', 'file_name')
    
    def task_link(self, obj):
        url = reverse('admin:myapp_task_change', args=[obj.task.id])
        return format_html('<a href=\"{}\">{}</a>', url, obj.task.title)
    task_link.short_description = 'Task'
    task_link.admin_order_field = 'task__title'
    
    def content_type_display(self, obj):
        return obj.content_type
    content_type_display.short_description = 'Content Type'

# Register models
admin.site.register(User, CustomUserAdmin)
admin.site.register(Department)
admin.site.register(Role)
admin.site.register(UserProfile)
admin.site.register(Project)
admin.site.register(Task, TaskAdmin)
admin.site.register(TaskAttachment, TaskAttachmentAdmin)