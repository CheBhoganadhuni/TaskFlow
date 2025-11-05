from django.contrib import admin
from django.urls import path, include
from django.views.generic import RedirectView
from tasks import views
from django.contrib.auth import views as auth_views

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', RedirectView.as_view(url='login/', permanent=False)),  # Redirect root URL
    path('', include('tasks.urls')),
    path('users/<int:user_id>/delete/', views.delete_user_view, name='delete_user'),
]
