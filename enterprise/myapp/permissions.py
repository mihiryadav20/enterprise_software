from rest_framework import permissions

class IsOperationsLeadOrStaff(permissions.BasePermission):
    """
    Custom permission to only allow Operations Leads or staff members to create projects.
    """
    message = 'Only Operations Leads and staff members can create projects.'

    def has_permission(self, request, view):
        # Allow all read permissions (GET, HEAD, OPTIONS)
        if request.method in permissions.SAFE_METHODS:
            return True
            
        # Check if user is staff
        if request.user.is_staff:
            return True
            
        # Check if user is an Operations Lead
        if hasattr(request.user, 'profile') and request.user.profile.role:
            return request.user.profile.role.name == 'operations_lead'
            
        return False
