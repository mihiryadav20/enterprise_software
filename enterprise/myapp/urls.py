from django.urls import path, include
from rest_framework.routers import DefaultRouter, SimpleRouter
from rest_framework_simplejwt.views import TokenRefreshView
from . import views
from .task_views import TaskViewSet, TaskAttachmentViewSet

# Create a router for our API endpoints
router = DefaultRouter()
router.register(r'users', views.UserViewSet, basename='user')
router.register(r'projects', views.ProjectViewSet, basename='project')

# Staff-only endpoints
staff_router = DefaultRouter()
staff_router.register(r'departments', views.DepartmentViewSet, basename='department')
staff_router.register(r'roles', views.RoleViewSet, basename='role')

# Task endpoints - using SimpleRouter to avoid conflicts with the main router
task_router = SimpleRouter()
task_router.register(r'', TaskViewSet, basename='task')

# Task attachment endpoints
task_attachment_router = SimpleRouter()
task_attachment_router.register(
    r'attachments', 
    TaskAttachmentViewSet, 
    basename='task-attachment'
)

urlpatterns = [
    # Authentication endpoints
    path('auth/login/', views.LoginView.as_view(), name='login'),
    path('auth/logout/', views.LogoutView.as_view(), name='logout'),
    path('auth/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    
    # Current user profile
    path('users/me/', views.UserDetailView.as_view(), name='current-user-detail'),
    
    # Task endpoints
    path('projects/<int:project_id>/tasks/', include([
        # Task list/create/detail/update/delete
        path('', include(task_router.urls)),
        
        # Task attachments
        path('<int:task_id>/attachments/', include(task_attachment_router.urls)),
    ])),
    
    # Staff-only endpoints
    path('staff/', include(staff_router.urls)),
    
    # Include router URLs
    path('', include(router.urls)),
]