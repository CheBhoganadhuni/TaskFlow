# Django core
from django.shortcuts import render, redirect, get_object_or_404
from django.http import JsonResponse, HttpResponse, FileResponse, HttpResponseForbidden
from django.urls import reverse
from django.utils import timezone
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST, require_http_methods
from django.views.decorators.cache import never_cache

# Django auth
from django.contrib import messages
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.decorators import login_required
from django.contrib.admin.views.decorators import staff_member_required
from django.contrib.auth.forms import AuthenticationForm, PasswordResetForm
from django.contrib.auth.models import User
from django.db.models import Prefetch

# Models & forms
from .models import Task, Profile, Comment, Notification, TaskOrder
from .forms import (
    SignUpForm, TaskForm, SearchForm, CommentForm, UserDeleteForm
)

# Email
from django.core.mail import send_mail
from django.conf import settings

# Data processing / utils
from datetime import date
import json

# Matplotlib (for charts)
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

# PDF / report generation
import io
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Table, TableStyle,
    Spacer, Image, KeepTogether
)
from reportlab.graphics.shapes import Drawing
from reportlab.graphics import renderPDF

# HTML to PDF
from django.template.loader import render_to_string
import weasyprint
import base64


def login_view(request):
    if request.user.is_authenticated:
        return redirect('dashboard')

    if request.method == 'POST':
        if 'login_submit' in request.POST:
            login_form = AuthenticationForm(request, data=request.POST)
            signup_form = SignUpForm()  # unbound to avoid errors showing on signup form
            if login_form.is_valid():
                login(request, login_form.get_user())
                return redirect('dashboard')
        elif 'signup_submit' in request.POST:
            signup_form = SignUpForm(request.POST)
            login_form = AuthenticationForm()  # unbound to avoid errors on login form
            if signup_form.is_valid():
                user = signup_form.save()
                login(request, user)
                return redirect('dashboard')
    else:
        login_form = AuthenticationForm()
        signup_form = SignUpForm()

    context = {
        'form': login_form,
        'signup_form': signup_form,
    }
    return render(request, 'tasks/login.html', context)

def logout_view(request):
    logout(request)
    return redirect('login')

def password_reset_view(request):
    if request.method == 'POST':
        form = PasswordResetForm(request.POST)
        if form.is_valid():
            form.save(
                request=request,
                use_https=request.is_secure(),
                email_template_name='tasks/password_reset_email.html'
            )
            return redirect('login')
    else:
        form = PasswordResetForm()
    return render(request, 'tasks/password_reset.html', {'form': form})

@never_cache
@login_required
def user_list_view(request):
    profile = request.user.profile
    if profile.role == 'Manager':
        users = User.objects.filter(profile__manager=request.user).exclude(profile__role='Manager')
    elif request.user.is_superuser:
        users = User.objects.all()
    else:
        users = User.objects.none()
    return render(request, 'tasks/user_list.html', {'users': users})

@staff_member_required
@never_cache
@require_http_methods(["GET", "POST"])
def delete_user_view(request, user_id):
    profile = Profile.objects.get(user=request.user)
    if profile.role != 'Manager':
        messages.error(request, "You don't have permission to delete users.")
        return redirect('dashboard')

    user_to_delete = get_object_or_404(User, pk=user_id)

    if request.method == 'POST':
        form = UserDeleteForm(request.POST)
        if form.is_valid():
            reason = form.cleaned_data.get('reason', '').strip()
            send_email = form.cleaned_data.get('send_email', False)

            if send_email:
                subject = "Your account has been deleted"
                message = f"Dear {user_to_delete.username},\n\nYour account has been deleted by a Manager."
                if reason:
                    message += f"\n\nReason provided:\n{reason}"
                message += "\n\nIf you have any questions, contact your administrator."
                send_mail(subject, message, 'admin@taskflow.local', [user_to_delete.email], fail_silently=True)

            user_to_delete.delete()

            if request.headers.get('x-requested-with') == 'XMLHttpRequest':
                # AJAX request: return JSON success response
                return JsonResponse({'success': True})
            else:
                # Normal POST: redirect with message
                messages.success(request, f"User '{user_to_delete.username}' deleted and notified by email." if send_email else f"User '{user_to_delete.username}' deleted.")
                return redirect('user_list')
    else:
        form = UserDeleteForm()

    return render(request, 'tasks/delete_user.html', {'form': form, 'user_to_delete': user_to_delete})

def get_employee_and_chart_data(user, selected_user_id=None):
    profile = Profile.objects.select_related('manager').get(user=user)

    # Determine manager for filtering employees
    if profile.role == 'Employee':
        manager_user = profile.manager
    else:  # user is Manager
        manager_user = user

    # Filter only employees under the manager_user (exclude managers)
    # Assuming Profile.role stores "Employee" or "Manager"
    employee_qs = User.objects.filter(
        profile__manager=manager_user,
        profile__role='Employee'  # Only employees, exclude managers
    )

    selected_user = None
    if selected_user_id:
        try:
            selected_user = employee_qs.get(id=selected_user_id)
        except User.DoesNotExist:
            selected_user = None
    else:
        selected_user = employee_qs.first() if employee_qs.exists() else None

    chart_data_status = {'Pending': 0, 'Completed': 0, 'Overdue': 0}
    chart_data_priority = {'High': 0, 'Medium': 0, 'Low': 0}
    today = timezone.localdate()

    if selected_user:
        tasks = Task.objects.filter(assigned_to=selected_user)
        chart_data_status['Pending'] = tasks.filter(status='Pending', due_date__gt=today).count()
        chart_data_status['Completed'] = tasks.filter(status='Completed').count()
        chart_data_status['Overdue'] = tasks.filter(status='Pending', due_date__lte=today).count()

        chart_data_priority['High'] = tasks.filter(priority='High').count()
        chart_data_priority['Medium'] = tasks.filter(priority='Medium').count()
        chart_data_priority['Low'] = tasks.filter(priority='Low').count()

    return employee_qs, selected_user, chart_data_status, chart_data_priority

@login_required
def dashboard(request):
    selected_user_id = request.GET.get('employee')
    employee_qs, selected_user, chart_data_status, chart_data_priority = get_employee_and_chart_data(request.user, selected_user_id)
    
    return render(request, 'tasks/dashboard.html', {
        'employee_qs': employee_qs,
        'selected_user': selected_user,
        'chart_data_status': chart_data_status,
        'chart_data_priority': chart_data_priority,
    })

@login_required
def export_dashboard_pdf(request):
    selected_user_id = request.GET.get('employee')
    employee_qs, selected_user, status_counts, priority_counts = get_employee_and_chart_data(request.user, selected_user_id)

    if selected_user:
        tasks = Task.objects.filter(assigned_to=selected_user).prefetch_related('comments').all()
    else:
        tasks = Task.objects.none()
    
    today = timezone.localdate()
    for task in tasks:
        task.is_overdue = (
            task.status == 'Pending' and
            task.due_date is not None and
            task.due_date <= today
        )

    def generate_pie_chart(data_dict, title, colors_list):
        # If all values are zero or dict is empty, add dummy data to avoid NaN error
        if not data_dict or all(v == 0 for v in data_dict.values()):
            data_dict = {'No data': 1}
            colors_list = ['#cccccc']  # gray color for no data

        plt.figure(figsize=(3, 3))
        labels = list(data_dict.keys())
        sizes = list(data_dict.values())
        plt.pie(sizes, labels=labels, autopct='%1.0f%%', colors=colors_list, startangle=140, textprops={'fontsize': 9})
        plt.title(title, fontsize=12)
        plt.tight_layout()
        buf = io.BytesIO()
        plt.savefig(buf, format='PNG')
        plt.close()
        buf.seek(0)
        return base64.b64encode(buf.read()).decode()

    status_colors = ['#f1c40f', '#2ecc71', '#e74c3c']  # Pending, Completed, Overdue
    priority_colors = ['#c0392b', '#f39c12', '#3498db']  # High, Medium, Low

    status_chart_base64 = generate_pie_chart(status_counts, 'Task Status', status_colors)
    priority_chart_base64 = generate_pie_chart(priority_counts, 'Task Priority', priority_colors)

    html_string = render_to_string('tasks/export_dashboard_pdf.html', {
        'user': selected_user,
        'tasks': tasks,
        'status_chart_base64': f'data:image/png;base64,{status_chart_base64}',
        'priority_chart_base64': f'data:image/png;base64,{priority_chart_base64}',
        'no_tasks': len(tasks) == 0,
    })

    pdf_file = weasyprint.HTML(string=html_string).write_pdf()

    response = HttpResponse(pdf_file, content_type='application/pdf')
    filename = f'dashboard_report_{selected_user.username if selected_user else "unknown"}.pdf'
    response['Content-Disposition'] = f'attachment; filename={filename}'
    return response

@login_required
def task_list(request):
    profile = Profile.objects.select_related('manager').get(user=request.user)
    today = timezone.localdate()

    employee_ids = list(Profile.objects.filter(manager=profile.manager).values_list('user_id', flat=True))

    # Base queryset depending on role
    if profile.role == 'Employee':
        base_tasks = Task.objects.filter(created_by=profile.manager, assigned_to__in=employee_ids)
    elif profile.role == 'Manager':
        base_tasks = Task.objects.filter(created_by=request.user)
    else:
        base_tasks = Task.objects.filter(assigned_to=request.user)

    # Prefetch comments for efficiency
    base_tasks = base_tasks.prefetch_related(
        Prefetch('comments', queryset=Comment.objects.select_related('author'))
    )

    # Filter tasks using SearchForm before sorting, more efficient
    form = SearchForm(request.GET)
    if form.is_valid():
        if form.cleaned_data['title']:
            base_tasks = base_tasks.filter(title__icontains=form.cleaned_data['title'])
        if form.cleaned_data['priority']:
            base_tasks = base_tasks.filter(priority=form.cleaned_data['priority'])
        if form.cleaned_data['status']:
            status = form.cleaned_data['status']
            if status == 'Overdue':
                base_tasks = base_tasks.filter(status='Pending', due_date__lte=today)
            else:
                base_tasks = base_tasks.filter(status=status)

    tasks_list = list(base_tasks)

    # Attach is_overdue attribute for each task
    for task in tasks_list:
        task.is_overdue = (task.status == 'Pending' and task.due_date and task.due_date <= today)

    # Get user-specific saved order from TaskOrder
    user_orders = TaskOrder.objects.filter(user=request.user).order_by('position')
    order_map = {to.task_id: to.position for to in user_orders}

    # Sort tasks by saved order; tasks not in order_map go to end (order 9999)
    tasks_list.sort(key=lambda t: order_map.get(t.id, 9999))

    form_comment = CommentForm()

    return render(request, 'tasks/task_list.html', {
        'tasks': tasks_list,
        'form': form,
        'profile': profile,
        'today': today,
        'employee_ids': employee_ids,
        'form_comment': form_comment,
    })

@login_required
@require_POST
def mark_task_done(request, task_id):
    task = get_object_or_404(Task, id=task_id)
    if task.assigned_to != request.user:
        return HttpResponseForbidden("You do not have permission to modify this task.")

    if task.status != 'Completed':
        task.status = 'Completed'
        task.save()

        try:
            employee_profile = Profile.objects.get(user=task.assigned_to)
            manager = employee_profile.manager
        except Profile.DoesNotExist:
            manager = None

        if manager:
            Notification.objects.create(
                user=manager,
                message=f"Task '{task.title}' was completed by {task.assigned_to.username}.",
                read=False,
            )

    return redirect('task_list')

@login_required
def task_detail(request, pk):
    # Get the task or 404
    task = get_object_or_404(Task, pk=pk)
    # Get profile of current user
    profile = Profile.objects.get(user=request.user)

    # Permission checks:
    if profile.role == 'Manager':
        # Manager can see tasks created by self or employees
        allowed_user_ids = [request.user.id] + list(request.user.employees.values_list('id', flat=True))
        if task.created_by_id not in allowed_user_ids:
            return redirect('task_list')
    else:
        # Non-managers can see tasks only if assigned to them
        if task.assigned_to != request.user:
            return redirect('task_list')

    comments = task.comments.select_related('author').all()
    form = CommentForm(request.POST or None)

    # Handle POST comment submission
    if request.method == 'POST' and form.is_valid():
        comment = form.save(commit=False)
        comment.author = request.user
        comment.task = task
        comment.save()
        return redirect('task_detail', pk=pk)

    context = {
        'task': task,
        'profile': profile,
        'comments': comments,
        'form': form,
    }

    # If AJAX request, return partial template for modal content only
    if request.headers.get('x-requested-with') == 'XMLHttpRequest':
        return render(request, 'tasks/task_detail.html', context)

    # Regular full page render
    return render(request, 'tasks/task_detail.html', context)

@login_required
def task_create(request):
    profile = Profile.objects.get(user=request.user)
    if profile.role != 'Manager':
        # Only managers can create tasks
        return redirect('task_list')

    if request.method == 'POST':
        form = TaskForm(request.POST)
        form.fields['assigned_to'].queryset = User.objects.filter(profile__manager=request.user)
        if form.is_valid():
            task = form.save(commit=False)
            task.created_by = request.user
            task.save()

            assigned_user = task.assigned_to  # if ForeignKey, else adjust
            Notification.objects.create(
                user=assigned_user,
                task=task,
                message=f"New task assigned: {task.title}"
            )

            if request.headers.get('x-requested-with') == 'XMLHttpRequest':
                return JsonResponse({'success': True})

            return redirect('dashboard')
        else:
            if request.headers.get('x-requested-with') == 'XMLHttpRequest':
                html_form = render_to_string('tasks/task_form_partial.html', {'form': form}, request=request)
                return JsonResponse({'success': False, 'html_form': html_form})
    else:
        form = TaskForm()
        form.fields['assigned_to'].queryset = User.objects.filter(profile__manager=request.user)

    if request.headers.get('x-requested-with') == 'XMLHttpRequest':
        html_form = render_to_string('tasks/task_form_partial.html', {'form': form}, request=request)
        return HttpResponse(html_form)

    return render(request, 'tasks/task_form.html', {'form': form})


@login_required
def task_update(request, pk):
    task = get_object_or_404(Task, pk=pk)
    profile = Profile.objects.get(user=request.user)

    if profile.role == 'Employee':
        if task.assigned_to != request.user:
            return redirect('task_list')
    elif profile.role == 'Manager':
        allowed_user_ids = [request.user.id] + list(request.user.employees.values_list('id', flat=True))
        if task.created_by_id not in allowed_user_ids:
            return redirect('task_list')

    if request.method == 'POST':
        form = TaskForm(request.POST, instance=task)
        if form.is_valid():
            task = form.save()
            
            if task.status == 'Completed':
                send_mail(
                    'Task Completed',
                    f'Task "{task.title}" just completed.',
                    'from@example.com',
                    [task.created_by.email],
                )
            return redirect('task_list')
    else:
        form = TaskForm(instance=task)
    return render(request, 'tasks/task_form.html', {'form': form})

@login_required
def task_delete(request, pk):
    task = get_object_or_404(Task, pk=pk)
    profile = Profile.objects.get(user=request.user)

    if profile.role != 'Manager':
        messages.error(request, "You don't have permission to delete tasks.")
        return redirect('task_list')

    # managers can only delete their own or their employees' tasks
    allowed_user_ids = [request.user.id] + list(request.user.employees.values_list('id', flat=True))
    if task.created_by_id not in allowed_user_ids:
        messages.error(request, "You don't have permission to delete this task.")
        return redirect('task_list')

    if request.method == 'POST':
        task.delete()
        messages.success(request, "Task deleted successfully.")
        return redirect('task_list')
    return render(request, 'tasks/task_confirm_delete.html', {'task': task})

@login_required
def notifications_api(request):
    notifications = Notification.objects.filter(user=request.user).order_by('-created_at')[:20]
    data = {
        'notifications': [
            {
                'id': n.id,
                'message': n.message,
                'task_id': n.task.id if n.task else None,
                'created_at': n.created_at.strftime('%Y-%m-%d %H:%M'),
            }
            for n in notifications
        ],
        'unread_count': notifications.count(),
    }
    return JsonResponse(data)


@login_required
@require_POST
def dismiss_notification(request, notif_id):
    notif = get_object_or_404(Notification, id=notif_id, user=request.user)
    notif.delete()
    return JsonResponse({'status': 'success'})

from django.views.decorators.http import require_POST

@login_required
@require_POST
def add_comment(request, task_id):
    task = get_object_or_404(Task, id=task_id)
    # Permission check skipped, assuming visibility is already enforced
    form = CommentForm(request.POST)
    if form.is_valid():
        comment = form.save(commit=False)
        comment.author = request.user
        comment.task = task
        comment.save()
    return redirect('task_list')  # or redirect to task detail if needed

@login_required
@csrf_exempt
def update_task_order(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            orders = data.get('order', [])
            user = request.user

            for item in orders:
                task_id = int(item['id'])
                pos = int(item['order'])
                task = Task.objects.get(id=task_id)  # optionally check ownership if needed
                task_order, created = TaskOrder.objects.get_or_create(user=user, task=task)
                task_order.position = pos
                task_order.save()

            return JsonResponse({'success': True})
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)})

    return JsonResponse({'success': False, 'error': 'Invalid request'})
