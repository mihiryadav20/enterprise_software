import os
import tempfile
from datetime import datetime, timedelta

from django.contrib.auth import get_user_model
from django.test import TestCase, override_settings
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient, APITestCase
from rest_framework_simplejwt.tokens import RefreshToken

from myapp.models import Department, Project, Task, TaskAttachment, TaskPriority, TaskStatus

# Get the User model
User = get_user_model()

# Use a temporary directory for file uploads during tests
MEDIA_ROOT = tempfile.mkdtemp()


@override_settings(MEDIA_ROOT=MEDIA_ROOT)
class TaskAPITestCase(APITestCase):
    """Test suite for the Task API endpoints."""

    def setUp(self):
        """Set up test data."""
        # Create test users
        self.admin = User.objects.create_superuser(
            username='admin',
            email='admin@example.com',
            password='testpass123',
            is_staff=True
        )
        
        self.user1 = User.objects.create_user(
            username='user1',
            email='user1@example.com',
            password='testpass123'
        )
        
        self.user2 = User.objects.create_user(
            username='user2',
            email='user2@example.com',
            password='testpass123'
        )
        
        # Create a department
        self.department = Department.objects.create(
            name='Engineering',
            description='Engineering Department'
        )
        
        # Create a project
        self.project = Project.objects.create(
            name='Test Project',
            description='A test project',
            department=self.department,
            created_by=self.admin
        )
        
        # Create some test tasks
        self.task1 = Task.objects.create(
            title='Task 1',
            description='First test task',
            project=self.project,
            assignee=self.user1,
            created_by=self.admin,
            due_date=datetime.now() + timedelta(days=7),
            priority=TaskPriority.HIGH,
            status=TaskStatus.TODO
        )
        
        self.task2 = Task.objects.create(
            title='Task 2',
            description='Second test task',
            project=self.project,
            assignee=self.user2,
            created_by=self.admin,
            due_date=datetime.now() + timedelta(days=14),
            priority=TaskPriority.MEDIUM,
            status=TaskStatus.IN_PROGRESS
        )
        
        # Create API clients
        self.admin_client = APIClient()
        self.user1_client = APIClient()
        self.user2_client = APIClient()
        
        # Authenticate clients
        self._authenticate_user(self.admin_client, self.admin)
        self._authenticate_user(self.user1_client, self.user1)
        self._authenticate_user(self.user2_client, self.user2)
    
    def _authenticate_user(self, client, user):
        """Helper method to authenticate a test client with a user."""
        refresh = RefreshToken.for_user(user)
        client.credentials(HTTP_AUTHORIZATION=f'Bearer {refresh.access_token}')
    
    def test_create_task(self):
        """Test creating a new task."""
        url = reverse('task-list')
        data = {
            'title': 'New Task',
            'description': 'A new test task',
            'project': self.project.id,
            'assignee': self.user1.id,
            'due_date': (datetime.now() + timedelta(days=5)).isoformat(),
            'priority': TaskPriority.HIGH,
            'status': TaskStatus.TODO
        }
        
        response = self.admin_client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Task.objects.count(), 3)
        self.assertEqual(Task.objects.get(id=response.data['id']).title, 'New Task')
    
    def test_retrieve_task(self):
        """Test retrieving a task."""
        url = reverse('task-detail', args=[self.task1.id])
        response = self.user1_client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['title'], self.task1.title)
    
    def test_update_task(self):
        """Test updating a task."""
        url = reverse('task-detail', args=[self.task1.id])
        data = {'title': 'Updated Task Title'}
        
        response = self.admin_client.patch(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.task1.refresh_from_db()
        self.assertEqual(self.task1.title, 'Updated Task Title')
    
    def test_delete_task(self):
        """Test deleting a task."""
        url = reverse('task-detail', args=[self.task1.id])
        response = self.admin_client.delete(url)
        
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertEqual(Task.objects.count(), 1)
    
    def test_task_attachment_upload(self):
        """Test uploading an attachment to a task."""
        url = reverse('task-attachments', args=[self.task1.id])
        
        # Create a test file
        with tempfile.NamedTemporaryFile(suffix='.txt', delete=False) as tmp_file:
            tmp_file.write(b'Test file content')
            tmp_file_path = tmp_file.name
        
        try:
            with open(tmp_file_path, 'rb') as file:
                response = self.user1_client.post(url, {'file': file}, format='multipart')
            
            self.assertEqual(response.status_code, status.HTTP_201_CREATED)
            self.assertEqual(TaskAttachment.objects.count(), 1)
            attachment = TaskAttachment.objects.first()
            self.assertEqual(attachment.task, self.task1)
            self.assertEqual(attachment.uploaded_by, self.user1)
            
        finally:
            # Clean up the test file
            if os.path.exists(tmp_file_path):
                os.unlink(tmp_file_path)
    
    def test_task_status_workflow(self):
        """Test the task status workflow."""
        url = reverse('task-detail', args=[self.task1.id])
        
        # Move task to IN_PROGRESS
        response = self.user1_client.patch(
            url,
            {'status': TaskStatus.IN_PROGRESS},
            format='json'
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.task1.refresh_from_db()
        self.assertEqual(self.task1.status, TaskStatus.IN_PROGRESS)
        
        # Move task to DONE
        response = self.user1_client.patch(
            url,
            {'status': TaskStatus.DONE},
            format='json'
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.task1.refresh_from_db()
        self.assertEqual(self.task1.status, TaskStatus.DONE)
        self.assertIsNotNone(self.task1.completed_at)
    
    def test_task_permissions(self):
        """Test task permissions."""
        # User2 should not be able to update user1's task
        url = reverse('task-detail', args=[self.task1.id])
        response = self.user2_client.patch(
            url,
            {'title': 'Unauthorized Update'},
            format='json'
        )
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        
        # But user1 should be able to update their own task
        response = self.user1_client.patch(
            url,
            {'title': 'Authorized Update'},
            format='json'
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
    
    def test_task_filtering(self):
        """Test filtering tasks by status and assignee."""
        # Filter by status
        response = self.user1_client.get(
            reverse('task-list'),
            {'status': TaskStatus.TODO}
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]['id'], self.task1.id)
        
        # Filter by assignee
        response = self.admin_client.get(
            reverse('task-list'),
            {'assignee': self.user2.id}
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]['id'], self.task2.id)
    
    def tearDown(self):
        """Clean up after tests."""
        # Clean up any files created during tests
        for task_attachment in TaskAttachment.objects.all():
            if os.path.exists(task_attachment.file.path):
                os.remove(task_attachment.file.path)
        
        # Remove the temporary directory
        if os.path.exists(MEDIA_ROOT):
            os.rmdir(MEDIA_ROOT)
