from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import Department, User, UserProfile

class CustomUserAdmin(UserAdmin):
    model = User
    list_display = ('username', 'email', 'first_name', 'last_name', 'is_staff')
    fieldsets = (
        (None, {'fields': ('username', 'password')}),
        ('Personal info', {'fields': ('first_name', 'last_name', 'email')}),
        ('Permissions', {'fields': ('is_active', 'is_staff', 'is_superuser')}),
        ('Important dates', {'fields': ('last_login', 'date_joined')}),
    )
    filter_horizontal = ()
    list_filter = ('is_staff', 'is_superuser', 'is_active')

admin.site.register(Department)
admin.site.register(User, CustomUserAdmin)
admin.site.register(UserProfile)