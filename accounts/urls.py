from django.urls import path
from . import views

app_name = 'accounts'

urlpatterns = [
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('dashboard/', views.dashboard, name='dashboard'),
    path('users/', views.user_list, name='user_list'),
    path('users/create/', views.user_create, name='user_create'),
    path('users/<int:pk>/edit/', views.user_edit, name='user_edit'),
    path('users/<int:pk>/delete/', views.user_delete, name='user_delete'),
    path('users/<int:pk>/toggle-active/', views.user_toggle_active, name='user_toggle_active'),
    path('users/<int:pk>/unlock/', views.user_unlock, name='user_unlock'),
    path('users/<int:pk>/reset-mfa/', views.user_reset_mfa, name='user_reset_mfa'),
    path('users/<int:pk>/toggle-mfa-exemption/', views.user_toggle_mfa_exemption, name='user_toggle_mfa_exemption'),
    path('audit-logs/', views.audit_log_list, name='audit_log_list'),
    path('verify-mfa/', views.verify_mfa, name='verify_mfa'),
    path('search/', views.global_search, name='global_search'),
    path('setup-mfa/', views.setup_mfa, name='setup_mfa'),
    path('confirm-mfa/', views.confirm_mfa_setup, name='confirm_mfa_setup'),
    path('toggle-mfa/', views.toggle_mfa, name='toggle_mfa'),
    path('forgot-password/', views.forgot_password, name='forgot_password'),
    path('reset-password/', views.reset_password, name='reset_password'),
    path('force-change-password/', views.force_change_password, name='force_change_password'),
]
