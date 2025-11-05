# models.py
from django.db import models
from django.contrib.auth.models import User

class Profile(models.Model):
    ROLE_CHOICES = (
        ('Manager', 'Manager'),
        ('Employee', 'Employee'),
    )
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    role = models.CharField(max_length=20, choices=ROLE_CHOICES)
    manager = models.ForeignKey(
        User, null=True, blank=True, on_delete=models.SET_NULL, related_name='employees'
    )

    def __str__(self):
        return f"{self.user.username} ({self.role})"
        
class Task(models.Model):
    PRIORITY_CHOICES = [('Low', 'Low'), ('Medium', 'Medium'), ('High', 'High')]
    STATUS_CHOICES = [('Pending', 'Pending')]

    title = models.CharField(max_length=100)
    description = models.TextField()
    due_date = models.DateField(null=True, blank=True)
    priority = models.CharField(max_length=10, choices=PRIORITY_CHOICES, default='Medium')
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='Pending')
    assigned_to = models.ForeignKey(User, on_delete=models.CASCADE, related_name='tasks')
    created_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='created_tasks')
    created_at = models.DateTimeField(auto_now_add=True)

    order = models.PositiveIntegerField(default=0)  # new field for task order

    class Meta:
        ordering = ['order']  # default ordering by order field

    def __str__(self):
        return self.title

class Notification(models.Model):
    user = models.ForeignKey(User, related_name='notifications', on_delete=models.CASCADE)
    task = models.ForeignKey('Task', null=True, blank=True, on_delete=models.CASCADE)
    message = models.CharField(max_length=255)
    read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Notification for {self.user.username}: {self.message}"
class Comment(models.Model):
    task = models.ForeignKey(Task, on_delete=models.CASCADE, related_name='comments')
    author = models.ForeignKey(User, on_delete=models.CASCADE)
    content = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['created_at']

    def __str__(self):
        return f"Comment by {self.author.username} on {self.task.title}"

class TaskOrder(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='task_orders')
    task = models.ForeignKey(Task, on_delete=models.CASCADE, related_name='orders')
    position = models.PositiveIntegerField(default=0)

    class Meta:
        unique_together = ('user', 'task')
        ordering = ['position']
