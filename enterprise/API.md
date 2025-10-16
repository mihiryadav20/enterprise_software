# Enterprise Project Management API Documentation

## Base URL
`http://127.0.0.1:8000/api/v1/`

## Authentication

### Login
- **URL**: `/auth/login/`
- **Method**: `POST`
- **Description**: Authenticate user and get JWT tokens
- **Request Body**:
  ```json
  {
    "username": "string",
    "password": "string"
  }
  ```
- **Response**:
  ```json
  {
    "refresh": "string",
    "access": "string"
  }
  ```
- **Authentication**: Not required

### Refresh Token
- **URL**: `/token/refresh/`
- **Method**: `POST`
- **Description**: Get a new access token using refresh token
- **Request Body**:
  ```json
  {
    "refresh": "string"
  }
  ```
- **Authentication**: Not required

## Projects

### List/Create Projects
- **URL**: `/projects/`
- **Method**: 
  - `GET`: List all projects (Requires authentication)
  - `POST`: Create new project (Requires admin/lead role)
- **Query Parameters**:
  - `search`: Filter projects by name/description
  - `status`: Filter by project status
  - `page`: Page number for pagination
  - `page_size`: Number of items per page

### Project Detail
- **URL**: `/projects/<id>/`
- **Methods**: 
  - `GET`: Get project details
  - `PUT`: Update project (admin/lead only)
  - `DELETE`: Delete project (admin only)
- **URL Parameters**:
  - `id`: Project ID

### Add Project Members
- **URL**: `/projects/<id>/add-members/`
- **Method**: `POST`
- **Description**: Add members to project (admin/lead only)
- **Request Body**:
  ```json
  {
    "user_ids": [1, 2, 3],
    "role": "member"
  }
  ```

## Tasks

### List/Create Tasks
- **URL**: `/projects/<project_id>/tasks/`
- **Method**:
  - `GET`: List all tasks in project
  - `POST`: Create new task
- **Request Body (POST)**:
  ```json
  {
    "title": "string",
    "description": "string",
    "status": "todo|in_progress|in_review|done|blocked",
    "priority": "low|medium|high|critical",
    "assignees": [user_id1, user_id2],
    "due_date": "YYYY-MM-DDTHH:MM:SSZ"
  }
  ```

### Task Detail
- **URL**: `/projects/<project_id>/tasks/<id>/`
- **Methods**:
  - `GET`: Get task details
  - `PUT`: Update task
  - `PATCH`: Partially update task
  - `DELETE`: Delete task (admin/lead only)

### Task Assignment
- **URL**: `/projects/<project_id>/tasks/<id>/assign/`
- **Method**: `POST`
- **Description**: Assign users to task
- **Request Body**:
  ```json
  {
    "user_ids": [1, 2]
  }
  ```

### Set Lead Assignee
- **URL**: `/projects/<project_id>/tasks/<id>/set-lead/`
- **Method**: `POST`
- **Description**: Set lead assignee for task
- **Request Body**:
  ```json
  {
    "user_id": 1
  }
  ```

### Task Attachments
- **List/Create**: `POST /projects/<project_id>/tasks/<task_id>/attachments/`
- **Detail/Delete**: `GET/DELETE /projects/<project_id>/tasks/<task_id>/attachments/<id>/`

## Permissions

### Authentication Required
All endpoints except `/auth/login/` and `/token/refresh/` require authentication using JWT token in the header:
```
Authorization: Bearer <access_token>
```

### Role-Based Access
- **Admin**: Full access to all resources
- **Lead**: Full access to their projects/tasks, limited access to others
- **Member**: Read-only access to assigned tasks, limited write access

## Error Responses

### 401 Unauthorized
```json
{
  "detail": "Authentication credentials were not provided."
}
```

### 403 Forbidden
```json
{
  "detail": "You do not have permission to perform this action."
}
```

### 404 Not Found
```json
{
  "detail": "Not found."
}
```