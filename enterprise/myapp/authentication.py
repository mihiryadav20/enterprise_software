from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework import exceptions

class JWTAuthenticationSafe(JWTAuthentication):
    def authenticate(self, request):
        try:
            return super().authenticate(request)
        except exceptions.AuthenticationFailed:
            return None
