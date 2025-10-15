from django.urls import path, include
from rest_framework.routers import DefaultRouter
from rest_framework_simplejwt.views import TokenRefreshView
from . import views

# Create a router for our API endpoints
router = DefaultRouter()
router.register(r'users', views.UserViewSet, basename='user')

# Staff-only endpoints
staff_router = DefaultRouter()
staff_router.register(r'departments', views.DepartmentViewSet, basename='department')
staff_router.register(r'roles', views.RoleViewSet, basename='role')

urlpatterns = [
    # Authentication endpoints
    path('auth/login/', views.LoginView.as_view(), name='login'),
    path('auth/logout/', views.LogoutView.as_view(), name='logout'),
    path('auth/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    
    # Current user profile
    path('users/me/', views.UserDetailView.as_view(), name='current-user-detail'),
    
    # Staff-only endpoints
    path('staff/', include(staff_router.urls)),
    
    # Include router URLs
    path('', include(router.urls)),
]