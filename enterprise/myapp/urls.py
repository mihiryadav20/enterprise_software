from django.urls import path, include
from rest_framework.routers import DefaultRouter
from rest_framework_simplejwt.views import (
    TokenObtainPairView,
    TokenRefreshView,
    TokenVerifyView,
    TokenBlacklistView
)
from . import views

# Create a router for our API endpoints
router = DefaultRouter()
router.register(r'users', views.UserViewSet, basename='user')
router.register(r'departments', views.DepartmentViewSet, basename='department')
router.register(r'roles', views.RoleViewSet, basename='role')

# JWT Authentication URLs
jwt_urlpatterns = [
    path('token/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('token/verify/', TokenVerifyView.as_view(), name='token_verify'),
    path('token/blacklist/', TokenBlacklistView.as_view(), name='token_blacklist'),
]

# Combine all URL patterns
urlpatterns = [
    # API v1
    path('v1/', include([
        # JWT Authentication
        path('auth/', include(jwt_urlpatterns)),
        
        # API endpoints
        path('', include(router.urls)),
        
        # Additional custom endpoints
        path('profile/', views.UserProfileView.as_view(), name='user-profile'),
    ])),
    
    # Browsable API login/logout
    path('api-auth/', include('rest_framework.urls', namespace='rest_framework')),
]

# Add URL patterns for the browsable API
urlpatterns += router.urls