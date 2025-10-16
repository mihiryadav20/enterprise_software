import os
import tempfile
from datetime import timedelta
from django.urls import reverse
from django.utils import timezone
from rest_framework import status
from rest_framework.test import APITestCase, APIClient
from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile

from .models import Project, ProjectMember, Task, TaskAttachment, TaskStatus, TaskPriority

User = get_user_model()


class TaskTests(APITestCase):
    def setUp(self):
        # Create test users
        self.user1 = User.objects.create_user(
            username='testuser1',
            email='test1@example.com',
            password='testpass123',
            first_name='Test',
            last_name='User1'
        )
        
        self.user2 = User.objects.create_user(
            username='testuser2',
            email='test2@example.com',
            password='testpass123',
            first_name='Test',
            last_name='User2'
        )
        
        # Create a project
        self.project = Project.objects.create(
            name='Test Project',
            description='A test project',
            status='active',
            start_date=timezone.now().date(),
            end_date=timezone.now().date() + timedelta(days=30)
        )
        
        # Add users to the project
        self.project_member1 = ProjectMember.objects.create(
            project=self.project,
            user=self.user1,
            role=ProjectMember.RoleChoices.MEMBER
        )
        
        self.project_member2 = ProjectMember.objects.create(
            project=self.project,
            user=self.user2,
            role=ProjectMember.RoleChoices.ADMIN
        )
        
        # Create a test task
        self.task = Task.objects.create(
            title='Test Task',
            description='A test task',
            project=self.project,
            assignee=self.user1,
            created_by=self.user2,
            due_date=timezone.now() + timedelta(days=7),
            priority=TaskPriority.MEDIUM,
            status=TaskStatus.TODO
        )
        
        # Set up the API client
        self.client = APIClient()
        
        # Login the user
        self.client.force_authenticate(user=self.user1)
        
        # Set up URLs
        self.task_list_url = reverse('task-list', kwargs={'project_id': self.project.id})
        self.task_detail_url = reverse('task-detail', kwargs={
            'project_id': self.project.id,
            'pk': self.task.id
        })
    
    def test_create_task(self):
        """Test creating a new task."""
        data = {
            'title': 'New Task',
            'description': 'A new task description',
            'project': self.project.id,
            'assignee': self.user1.id,
            'due_date': (timezone.now() + timedelta(days=14)).isoformat(),
            'priority': TaskPriority.HIGH,
            'status': TaskStatus.TODO
        }
        
        response = self.client.post(self.task_list_url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Task.objects.count(), 2)
        self.assertEqual(Task.objects.get(id=response.data['id']).title, 'New Task')
    
    def test_retrieve_task(self):
        """Test retrieving a task."""
        response = self.client.get(self.task_detail_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['title'], self.task.title)
    
    def test_update_task(self):
        """Test updating a task."""
        data = {
            'title': 'Updated Task Title',
            'description': 'Updated description',
            'status': TaskStatus.IN_PROGRESS
        }
        
        # Only the assignee or creator can update the task
        self.client.force_authenticate(user=self.user1)  # assignee
        response = self.client.patch(self.task_detail_url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.task.refresh_from_db()
        self.assertEqual(self.task.title, 'Updated Task Title')
        self.assertEqual(self.task.status, TaskStatus.IN_PROGRESS)
    
    def test_delete_task(self):
        """Test deleting a task."""
        # Only the creator can delete the task
        self.client.force_authenticate(user=self.user2)  # creator
        response = self.client.delete(self.task_detail_url)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertEqual(Task.objects.count(), 0)
    
    def test_task_attachment_upload(self):
        """Test uploading an attachment to a task."""
        # Create a test file
        test_file = SimpleUploadedFile(
            'test_file.txt',
            b'This is a test file',
            content_type='text/plain'
        )
        
        # Upload the file
        upload_url = reverse('task-attachment-list', kwargs={
            'project_id': self.project.id,
            'task_id': self.task.id
        })
        
        response = self.client.post(upload_url, {'file': test_file}, format='multipart')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(TaskAttachment.objects.count(), 1)
        self.assertEqual(TaskAttachment.objects.first().file_name, 'test_file.txt')
    
    def test_task_status_change(self):
        """Test changing a task's status."""
        status_url = f"{self.task_detail_url}change-status/"
        
        # Change status to IN_PROGRESS
        response = self.client.post(
            status_url,
            {'status': TaskStatus.IN_PROGRESS},
            format='json'
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.task.refresh_from_db()
        self.assertEqual(self.task.status, TaskStatus.IN_PROGRESS)
        
        # Change status to DONE (should set completed_at)
        response = self.client.post(
            status_url,
            {'status': TaskStatus.DONE},
            format='json'
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.task.refresh_from_db()
        self.assertEqual(self.task.status, TaskStatus.DONE)
        self.assertIsNotNone(self.task.completed_at)
    
    def test_task_assign(self):
        """Test assigning a task to another user."""
        assign_url = f"{self.task_detail_url}assign/"
        
        # Assign to user2
        response = self.client.post(
            assign_url,
            {'user_id': self.user2.id},
            format='json'
        )
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.task.refresh_from_db()
        self.assertEqual(self.task.assignee, self.user2)
    
    def test_task_filtering(self):
        """Test filtering tasks by various parameters."""
        # Create some test tasks
        Task.objects.create(
            title='High Priority Task',
            project=self.project,
            assignee=self.user1,
            created_by=self.user2,
            priority=TaskPriority.HIGH,
            status=TaskStatus.TODO
        )
        
        Task.objects.create(
            title='In Progress Task',
            project=self.project,
            assignee=self.user2,
            created_by=self.user1,
            priority=TaskPriority.MEDIUM,
            status=TaskStatus.IN_PROGRESS
        )
        
        # Test filtering by status
        response = self.client.get(self.task_list_url, {'status': TaskStatus.IN_PROGRESS})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]['status'], TaskStatus.IN_PROGRESS)
        
        # Test filtering by assignee
        response = self.client.get(self.task_list_url, {'assignee_id': self.user2.id})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]['assignee'], self.user2.id)
        
        # Test filtering by priority
        response = self.client.get(self.task_list_url, {'priority': TaskPriority.HIGH})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]['priority'], TaskPriority.HIGH)
    
    def test_task_permissions(self):
        """Test task permissions for different user roles."""
        # Create a non-member user
        non_member = User.objects.create_user(
            username='nonmember',
            email='nonmember@example.com',
            password='testpass123'
        )
        
        # Non-member should not be able to access project tasks
        self.client.force_authenticate(user=non_member)
        response = self.client.get(self.task_list_url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        
        # Member should be able to view tasks
        self.client.force_authenticate(user=self.user1)
        response = self.client.get(self.task_list_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Only task assignee or creator should be able to update
        response = self.client.patch(
            self.task_detail_url,
            {'title': 'Unauthorized Update'},
            format='json'
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Non-assignee/non-creator should not be able to update
        another_user = User.objects.create_user(
            username='anotheruser',
            email='another@example.com',
            password='testpass123'
        )
        self.client.force_authenticate(user=another_user)
        response = self.client.patch(
            self.task_detail_url,
            {'title': 'Unauthorized Update'},
            format='json'
        )
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
