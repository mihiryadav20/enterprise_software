from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth import get_user_model
from rest_framework import status
from rest_framework.test import APITestCase, APIClient
from rest_framework_simplejwt.tokens import RefreshToken

User = get_user_model()

class AuthenticationTests(APITestCase):
    def setUp(self):
        """Set up test data."""
        self.client = APIClient()
        self.login_url = reverse('login')
        self.logout_url = reverse('logout')
        self.refresh_url = reverse('token_refresh')
        
        # Create a test user
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123',
            first_name='Test',
            last_name='User'
        )
        self.user.is_active = True
        self.user.save()
        
        # Create a refresh token for the test user
        self.refresh = RefreshToken.for_user(self.user)
        
    def test_successful_login(self):
        """Test that a user can log in with valid credentials."""
        data = {
            'username': 'testuser',
            'password': 'testpass123'
        }
        response = self.client.post(self.login_url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('access', response.data)
        self.assertIn('refresh', response.data)
        self.assertIn('user', response.data)
        self.assertEqual(response.data['user']['username'], 'testuser')
        self.assertEqual(response.data['user']['email'], 'test@example.com')
    
    def test_login_invalid_credentials(self):
        """Test that login fails with invalid credentials."""
        data = {
            'username': 'testuser',
            'password': 'wrongpassword'
        }
        response = self.client.post(self.login_url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        # Updated to match your actual API response format
        self.assertIn('error', response.data)
        self.assertEqual(response.data['error'], 'Invalid credentials')
    
    def test_login_inactive_user(self):
        """Test that an inactive user cannot log in."""
        self.user.is_active = False
        self.user.save()
        
        data = {
            'username': 'testuser',
            'password': 'testpass123'
        }
        response = self.client.post(self.login_url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        # Updated to match your actual API response format
        self.assertIn('error', response.data)
        self.assertEqual(response.data['error'], 'Invalid credentials')
    
    def test_successful_logout(self):
        """Test that a user can log out successfully."""
        # Log in first
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.refresh.access_token}')
        
        # Log out
        data = {'refresh_token': str(self.refresh)}
        response = self.client.post(self.logout_url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_205_RESET_CONTENT)
        self.assertEqual(response.data, {"message": "Successfully logged out."})
    
    def test_logout_invalid_token(self):
        """Test that logout fails with an invalid token."""
        data = {'refresh_token': 'invalidtoken'}
        response = self.client.post(self.logout_url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('error', response.data)
    
    def test_refresh_token(self):
        """Test that a refresh token can be used to get a new access token."""
        data = {'refresh': str(self.refresh)}
        response = self.client.post(self.refresh_url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('access', response.data)
        self.assertIn('refresh', response.data)

    def test_protected_endpoint_after_logout(self):
        """Test that a protected endpoint is not accessible after logout."""
        # First, log in
        login_data = {
            'username': 'testuser',
            'password': 'testpass123'
        }
        login_response = self.client.post(self.login_url, login_data, format='json')
        access_token = login_response.data['access']
        refresh_token = login_response.data['refresh']
        
        # Access a protected endpoint - using the refresh endpoint as an example
        # Replace this with your actual protected endpoint if you have one
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {access_token}')
        
        # Test that we can access protected resources with valid token
        # Note: The refresh endpoint rotates tokens, so we get a new refresh token
        test_response = self.client.post(self.refresh_url, {'refresh': refresh_token}, format='json')
        self.assertEqual(test_response.status_code, status.HTTP_200_OK)
        
        # Get the NEW refresh token (the old one is now blacklisted due to rotation)
        new_refresh_token = test_response.data['refresh']
        
        # Now log out with the NEW refresh token (this blacklists it)
        logout_data = {'refresh_token': new_refresh_token}
        logout_response = self.client.post(self.logout_url, logout_data, format='json')
        self.assertEqual(logout_response.status_code, status.HTTP_205_RESET_CONTENT)
        
        # Try to use the blacklisted refresh token (should fail)
        refresh_response = self.client.post(self.refresh_url, {'refresh': new_refresh_token}, format='json')
        self.assertEqual(refresh_response.status_code, status.HTTP_401_UNAUTHORIZED)