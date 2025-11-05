from django.urls import path
from . import views
from django.contrib.auth import views as auth_views
from django.contrib.auth import views as auth_views
urlpatterns = [
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('dashboard/', views.dashboard, name='dashboard'),
    path('tasks/', views.task_list, name='task_list'),
    path('tasks/<int:pk>/', views.task_detail, name='task_detail'),
    path('tasks/create/', views.task_create, name='task_create'),
    path('tasks/<int:pk>/edit/', views.task_update, name='task_update'),
    path('tasks/<int:pk>/delete/', views.task_delete, name='task_delete'),
    path('password_reset/', views.password_reset_view, name='password_reset'),
    path('users/', views.user_list_view, name='user_list'),
    path('users/<int:user_id>/delete/', views.delete_user_view, name='delete_user'),
    path('users/', views.user_list_view, name='user_list'),
    path('users/<int:user_id>/delete/', views.delete_user_view, name='delete_user'),
    path('tasks/<int:task_id>/mark-done/', views.mark_task_done, name='mark_task_done'),
    path('notifications/api/', views.notifications_api, name='notifications_api'),
    path('notifications/dismiss/<int:notif_id>/', views.dismiss_notification, name='dismiss_notification'),
    path('notifications/mark-read/<int:notif_id>/', views.dismiss_notification, name='dismiss_notification'),
    path('tasks/<int:task_id>/add-comment/', views.add_comment, name='add_comment'),
    path('dashboard/export-pdf/', views.export_dashboard_pdf, name='export_dashboard_pdf'),
    path('password_reset/', auth_views.PasswordResetView.as_view(), name='password_reset'),
    path('password_reset/done/', auth_views.PasswordResetDoneView.as_view(), name='password_reset_done'),
    path('reset/<uidb64>/<token>/', auth_views.PasswordResetConfirmView.as_view(), name='password_reset_confirm'),
    path('reset/done/', auth_views.PasswordResetCompleteView.as_view(), name='password_reset_complete'),
    path('tasks/update-order/', views.update_task_order, name='update_task_order'),
]
