from django.urls import path, include
from rest_framework.routers import DefaultRouter
from rest_framework_simplejwt.views import TokenRefreshView
from . import views

# Create a router for our API endpoints
router = DefaultRouter()
router.register(r'users', views.UserViewSet, basename='user')
router.register(r'departments', views.DepartmentViewSet, basename='department')
router.register(r'roles', views.RoleViewSet, basename='role')

urlpatterns = [
    # Authentication endpoints
    path('auth/login', views.LoginView.as_view(), name='login'),
    path('auth/logout', views.LogoutView.as_view(), name='logout'),
    path('auth/refresh', TokenRefreshView.as_view(), name='token_refresh'),
    
    # User endpoints
    path('users/me', views.UserDetailView.as_view(), name='current-user-detail'),
    path('users/<str:username>', views.UserDetailView.as_view(), name='user-detail'),
    path('profile', views.UserProfileView.as_view(), name='user-profile'),
    
    # Include all router URLs
    path('', include(router.urls)),
]