from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from .models import Task
from .models import Profile
from django.core.exceptions import ValidationError
from .models import Comment
from django.conf import settings

class CommentForm(forms.ModelForm):
    content = forms.CharField(
        label='',
        widget=forms.Textarea(attrs={'rows': 3, 'placeholder': 'Add your comment here...'})
    )
    
    class Meta:
        model = Comment
        fields = ['content']

class TaskForm(forms.ModelForm):
    due_date = forms.DateField(
        widget=forms.DateInput(attrs={'type': 'date', 'class': 'form-control rounded'}),
        required=True,
        label="Due Date"
    )

    class Meta:
        model = Task
        fields = ['title', 'description', 'due_date', 'priority', 'status', 'assigned_to']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Add Bootstrap classes to all fields except due_date (already done)
        for field_name, field in self.fields.items():
            if field_name != 'due_date':
                css_class = 'form-control rounded'
                # for select fields use form-select (Bootstrap 5)
                if isinstance(field.widget, (forms.Select, forms.SelectMultiple)):
                    css_class = 'form-select rounded'
                # assign class
                existing_classes = field.widget.attrs.get('class', '')
                if existing_classes:
                    field.widget.attrs['class'] = existing_classes + ' ' + css_class
                else:
                    field.widget.attrs['class'] = css_class

from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
import re

class SignUpForm(UserCreationForm):
    email = forms.EmailField(required=True)
    manager_name = forms.CharField(
        required=True,
        max_length=150,
        label="Your Manager's Username",
        help_text='Enter SECRET CODE to register as Manager.'
    )

    class Meta:
        model = User
        fields = ('username', 'email', 'password1', 'password2', 'manager_name')

    def clean_username(self):
        username = self.cleaned_data.get('username')
        if not re.match(r'^[a-zA-Z][a-zA-Z0-9_]+$', username):
            raise ValidationError("Username must start with a letter and contain only letters, numbers, and underscores.")
        if User.objects.filter(username=username).exists():
            raise ValidationError("Username already exists.")
        return username

    def clean_email(self):
        email = self.cleaned_data.get('email')
        if User.objects.filter(email=email).exists():
            raise ValidationError("Email is already registered.")
        return email

    def clean_password2(self):
        password1 = self.cleaned_data.get('password1')
        password2 = self.cleaned_data.get('password2')
        if password1 and password2 and password1 != password2:
            raise ValidationError("Passwords don't match.")
        if password1 and (len(password1) < 8 or not re.search(r'\d', password1) or not re.search(r'[A-Za-z]', password1)):
            raise ValidationError("Password must be at least 8 characters and include both letters and digits.")
        return password2

    def clean_manager_name(self):
        manager_name = self.cleaned_data.get('manager_name', '').strip()
        invite_code = settings.MANAGER_INVITE_CODE

        if manager_name:
            # If manager_name matches the invite code, that's the manager registration path
            if manager_name == invite_code:
                return manager_name
            # Otherwise treat as username and validate existence
            elif not User.objects.filter(username=manager_name).exists():
                raise ValidationError('Manager username does not exist.')
        return manager_name

    def save(self, commit=True):
        user = super().save(commit=False)
        user.email = self.cleaned_data['email']
        user.set_password(self.cleaned_data['password1'])

        invite_code = settings.MANAGER_INVITE_CODE
        manager_name = self.cleaned_data.get('manager_name', '')

        if manager_name == invite_code:
            user.is_staff = True
            user.is_superuser = True
            role = 'Manager'
        else:
            user.is_staff = False
            user.is_superuser = False
            role = 'Employee'

        if commit:
            user.save()
            profile, _ = Profile.objects.get_or_create(user=user)
            profile.role = role
            if role == 'Employee' and manager_name and manager_name != invite_code:
                profile.manager = User.objects.get(username=manager_name)
            profile.save()

        return user



class SearchForm(forms.Form):
    title = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Task title'
        })
    )
    priority = forms.ChoiceField(
        choices=[('', 'Any')] + Task.PRIORITY_CHOICES,
        required=False,
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    status = forms.ChoiceField(
        choices=[('', 'Any')] + Task.STATUS_CHOICES,
        required=False,
        widget=forms.Select(attrs={'class': 'form-select'})
    )
from django import forms


class UserDeleteForm(forms.Form):
    reason = forms.CharField(
        required=False,
        widget=forms.Textarea(attrs={
            'rows': 3,
            'class': 'form-control rounded',
            'placeholder': 'Optional: Provide a reason for deleting the user',
            'style': 'resize: vertical;',
        }),
        label="Reason for deletion (optional)"
    )
    send_email = forms.BooleanField(
        required=False,
        initial=True,
        label="Send email notification to the user, Takes few Seconds",
        widget=forms.CheckboxInput(attrs={
            'class': 'form-check-input',
            'style': 'margin-left: 0;',  # Adjust checkbox spacing if needed
        })
    )