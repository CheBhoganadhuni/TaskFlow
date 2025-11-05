# TaskFlow
" TaskFlow - Task and User Management Web Application "

TaskFlow is a Django-based web application for managing tasks and users within an organization, supporting roles like Manager and Employee. It features a clean and intuitive UI with role-based access, detailed task tracking, commenting, email notifications, and PDF reporting.

## Features

- **User Roles and Management**
  - Managers can create and manage employees.
  - Only employees under a manager are displayed to that manager.
  - Secure permission checks to prevent unauthorized actions.
  - User deletion with optional email notification.
- **Authentication**
  - Secure login and signup.
  - Password reset with email notification.
  - User-friendly feedback during password reset process.
- **Task Management**
  - Create, update, delete tasks with priorities and due dates.
  - Tasks assigned to specific employees.
  - ‘Mark as Done’ option for employees and Overdue task detection and highlighting.
  - Real-time notifications for task updates and reminders within the application.
- **Comments and Collaboration**
  - Employees and managers can add comments per task.
  - Comments include author names and timestamps.
- **Dynamic UI and Modals**
  - AJAX-powered modal forms for user and task management.
  - Smooth modal transitions, including nested modals handling.
  - Intuitive drag-and-drop interface for prioritizing and organizing tasks.
  - Task order updates automatically saved and reflected across sessions.
- **Reports and Export**
  - Dashboard with charts showing task status and priority.
  - Export dashboard and task data as PDF with styled cards and charts.
- **Security and Usability**
  - Role-based access control ensures data privacy.
  - Email sent asynchronously to avoid UI delays.
  - Responsive and user-friendly interface built with Bootstrap.

## Database Setup (PostgreSQL):

If you use PostgreSQL, ensure:

1. PostgreSQL server is installed and running.
2. A database and user with access are created matching DB_NAME, DB_USER, and DB_PASSWORD.
3. The database user has sufficient privileges.
4. The host and port settings match your PostgreSQL configuration.
5. You can use tools like psql or PgAdmin for managing databases.

```
CREATE DATABASE your-database-name;
CREATE USER your-database-user WITH PASSWORD 'your-database-password';
GRANT ALL PRIVILEGES ON DATABASE your-database-name TO your-database-user;
```

## Environment Setup:

Create a `.env` file in the project root directory with the following environment variables:

1. SECRET_KEY=your-django-secret-key
2. DB_NAME=your-database-name
3. DB_USER=your-database-user
4. DB_PASSWORD=your-database-password
5. DB_HOST=your-database-host
6. DB_PORT=your-database-port
7. EMAIL_HOST_USER=your-email@example.com
8. EMAIL_HOST_PASSWORD=your-email-app-password  # For instance, use a Gmail app password, not your actual account password
9. MANAGER_INVITE_CODE=your-manager-invite-code

Replace the placeholders with your own values.

Make sure to keep this file private and **do not commit it to version control**.

## Installation

1. Clone the repository.
2. Create a Python virtual environment and activate it.
3. Install dependencies:
   pip install -r requirements.txt
4. Run migrations:
   python manage.py makemigrations
   python manage.py migrate
5. Create a superuser:
   python manage.py createsuperuser
6. Run the development server:
   python manage.py runserver
7. Access the app at `http://127.0.0.1:8000`

## Usage

- Log in as Manager or Employee to access respective functionalities.
- Manage tasks via the dashboard.
- Export reports as PDF.
- Reset password via email.

## Technologies

- Python 3.11
- Django 5.2
- Bootstrap 5 for UI
- WeasyPrint for PDF generation
- Chart.js for front-end charts

## Contributing

Contributions are welcome! Please submit a pull request or open an issue.

## License

[MIT License](LICENSE)
