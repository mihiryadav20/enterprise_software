from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

# Create a router for our API endpoints
router = DefaultRouter()
router.register(r'users', views.UserViewSet, basename='user')
router.register(r'departments', views.DepartmentViewSet, basename='department')
router.register(r'roles', views.RoleViewSet, basename='role')

urlpatterns = [
    # API endpoints
    path('users/me/', views.UserDetailView.as_view(), name='current-user-detail'),
    path('users/me', views.UserDetailView.as_view(), name='current-user-detail-noslash'),
    path('users/<str:username>/', views.UserDetailView.as_view(), name='user-detail'),
    path('users/<str:username>', views.UserDetailView.as_view(), name='user-detail-noslash'),
    path('profile/', views.UserProfileView.as_view(), name='user-profile'),
    
    # Include all router URLs
    path('', include(router.urls)),
]