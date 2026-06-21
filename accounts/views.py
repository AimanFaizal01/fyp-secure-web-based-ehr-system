from urllib import request

from django.shortcuts import render, redirect, get_object_or_404
from django.db.models import Q
from django.contrib.auth import authenticate, login, logout, update_session_auth_hash
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .models import User, AuditLog
from .forms import CustomUserCreationForm, CustomUserUpdateForm, LoginForm
from .decorators import admin_required
from .utils import log_action
from appointments.models import Appointment
from patients.models import Patient
from clinical.models import ClinicalNote
from django.utils import timezone
from datetime import timedelta
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError
import secrets


def login_view(request):
    if request.user.is_authenticated:
        return redirect('accounts:dashboard')
    
    if request.method == 'POST':
        form = LoginForm(request.POST)
        if form.is_valid():
            username = form.cleaned_data['username']
            password = form.cleaned_data['password']
            
            # Pre-check: Is user already locked?
            try:
                user_obj = User.objects.get(username=username)
                if user_obj.is_locked:
                    log_action(request, 'Login Blocked', is_suspicious=True,
                               details=f'Access denied for locked account: {username}')
                    messages.error(request, 'This account has been locked due to multiple failed attempts. Please contact an Administrator.')
                    return render(request, 'accounts/login.html', {'form': form})
            except User.DoesNotExist:
                user_obj = None
 
            user = authenticate(request, username=username, password=password)
            if user is not None:
                # Reset failed attempts on success
                user.failed_login_attempts = 0
                user.save()
                
                login(request, user)
                log_action(request, 'Login Success',
                           details=f'User {username} authenticated from {request.META.get("REMOTE_ADDR")}')
                messages.success(request, f'Welcome, {user.first_name or user.username}!')
                return redirect('accounts:dashboard')
            else:
                # Handle failure
                if user_obj:
                    user_obj.failed_login_attempts += 1
                    attempts_left = 5 - user_obj.failed_login_attempts
                    
                    if user_obj.failed_login_attempts >= 5:
                        user_obj.is_locked = True
                        details = f'ACCOUNT LOCKED: 5 failed attempts reached for user: {username}'
                        messages.error(request, 'Account locked. Too many failed attempts. Please contact an Administrator.')
                    else:
                        details = f'Failed login attempt {user_obj.failed_login_attempts}/5 for user: {username}'
                        messages.error(request, f'Invalid password. {attempts_left} attempt(s) remaining before account lockout.')
                    
                    user_obj.save()
                    log_action(request, 'Login Failed', is_suspicious=True, details=details)
                else:
                    log_action(request, 'Login Failed', is_suspicious=True, details=f'Invalid username: {username}')
                    messages.error(request, 'Invalid username or password.')
    else:
        form = LoginForm()
    return render(request, 'accounts/login.html', {'form': form})


def logout_view(request):
    # Capture username before logout
    user = request.user
    username = user.username if user.is_authenticated else "Session Expired"
    
    log_action(request, 'Logout', details=f'User {username} session ended.')
    logout(request)
    
    if request.GET.get('reason') == 'timeout':
        messages.warning(request, 'Your session has expired due to inactivity.')
    else:
        messages.info(request, 'You have been logged out.')
    return redirect('accounts:login')


@login_required
def dashboard(request):
    today = timezone.now().date()
    context = {
        'user': request.user,
        'today': today,
    }
    
    if request.user.is_admin:
        context['recent_logs'] = AuditLog.objects.all()[:5]
        context['suspicious_count'] = AuditLog.objects.filter(is_suspicious=True).count()
        context['total_users'] = User.objects.count()
        
    if request.user.is_receptionist or request.user.is_admin or request.user.is_doctor or request.user.is_nurse:
        context['today_appointments'] = Appointment.objects.filter(date=today).count()
        context['pending_appointments'] = Appointment.objects.filter(status='scheduled').count()

    if request.user.is_doctor or request.user.is_admin:
        context['my_recent_notes'] = ClinicalNote.objects.filter(doctor=request.user).count() if not request.user.is_admin else ClinicalNote.objects.count()
        context['total_patients'] = Patient.objects.filter(is_active=True).count()

    # Security Analytics (Last 7 Days)
    if request.user.is_admin:
        from django.db.models.functions import TruncDate
        from django.db.models import Count
        seven_days_ago = timezone.now().date() - timedelta(days=7)
        analytics_data = (
            AuditLog.objects.filter(timestamp__date__gte=seven_days_ago, is_suspicious=True)
            .annotate(day=TruncDate('timestamp'))
            .values('day')
            .annotate(count=Count('id'))
            .order_by('day')
        )
        
        # Format data for Chart.js
        chart_labels = []
        chart_values = []
        for i in range(7, -1, -1):
            day = timezone.now().date() - timedelta(days=i)
            chart_labels.append(day.strftime('%b %d'))
            val = next((item['count'] for item in analytics_data if item['day'] == day), 0)
            chart_values.append(val)
        
        # Use real suspicious audit log counts for graph
        context['chart_labels'] = chart_labels
        context['chart_values'] = chart_values

    log_action(request, 'View Dashboard')
    return render(request, 'accounts/dashboard.html', context)


@login_required
@admin_required
def user_list(request):
    users = User.objects.all().order_by('-date_joined')
    log_action(request, 'View User Management',
               details=f'Admin accessed user management panel. {users.count()} users in system.')
    return render(request, 'accounts/user_list.html', {'users': users})


@login_required
@admin_required
def user_create(request):
    if request.method == 'POST':
        form = CustomUserCreationForm(request.POST)
        if form.is_valid():
            new_user = form.save()
            log_action(request, 'Create User Account', resource='User', resource_id=new_user.id,
                       details=f'Staff account created: {new_user.username}')
            messages.success(request, f'User account for {new_user.username} created successfully. A password change will be required on their first login.')
            return redirect('accounts:user_list')
        else:
            messages.error(request, "Please correct the errors below.")
    else:
        form = CustomUserCreationForm()
    return render(request, 'accounts/user_form.html', {'form': form, 'title': 'Create User'})


@login_required
@admin_required
def user_edit(request, pk):
    user = get_object_or_404(User, pk=pk)
    if request.method == 'POST':
        form = CustomUserUpdateForm(request.POST, instance=user)
        if form.is_valid():
            user = form.save()
            log_action(request, 'Edit User Account', resource='User', resource_id=user.id,
                       details=f'Staff account updated: {user.username}')
            messages.success(request, 'User account updated successfully.')
            return redirect('accounts:user_list')
        else:
            messages.error(request, "Please correct the errors below.")
    else:
        form = CustomUserUpdateForm(instance=user)
    return render(request, 'accounts/user_form.html', {'form': form, 'title': 'Edit User'})


@login_required
@admin_required
def user_toggle_active(request, pk):
    user = get_object_or_404(User, pk=pk)
    user.is_active = not user.is_active
    # Also reset risk and lock if activating
    if user.is_active:
        user.is_locked = False
        user.security_risk_level = 0
        user.failed_login_attempts = 0
    user.save()
    status = 'activated and security reset' if user.is_active else 'deactivated'
    log_action(request, f'User {status}', resource='User', resource_id=user.id,
               details=f'Account {user.username} has been {status} by admin.')
    messages.success(request, f'User {user.username} has been {status}.')
    return redirect('accounts:user_list')


@login_required
@admin_required
def user_unlock(request, pk):
    user = get_object_or_404(User, pk=pk)
    user.is_locked = False
    user.security_risk_level = 0
    user.failed_login_attempts = 0
    user.save()
    log_action(request, 'User Unlocked', resource='User', resource_id=user.id,
               details=f'Account {user.username} has been manually unlocked and security cleared by admin.')
    messages.success(request, f'User {user.username} has been successfully unlocked and security metrics reset.')
    return redirect('accounts:user_list')


@login_required
@admin_required
def user_reset_mfa(request, pk):
    user = get_object_or_404(User, pk=pk)
    user.mfa_enabled = False
    user.totp_secret = None
    user.save()
    log_action(request, 'User MFA Reset', resource='User', resource_id=user.id,
               details=f'Multi-Factor Authentication reset for {user.username} by admin.')
    messages.success(request, f'MFA has been deactivated for {user.username}. They will receive a new setup wizard upon their next login.')
    return redirect('accounts:user_list')


@login_required
@admin_required
def user_toggle_mfa_exemption(request, pk):
    user = get_object_or_404(User, pk=pk)
    user.mfa_exempt = not user.mfa_exempt
    user.save()
    state = 'exempted from' if user.mfa_exempt else 'now required to use'
    log_action(request, 'User Exemption Toggled', resource='User', resource_id=user.id,
               details=f'MFA status toggled to {state} policy for {user.username} by admin.')
    messages.success(request, f'Security policy updated: {user.username} is {state} Multi-Factor verification.')
    return redirect('accounts:user_list')


@login_required
@admin_required
def user_delete(request, pk):
    user_to_delete = get_object_or_404(User, pk=pk)
    
    if user_to_delete == request.user:
        messages.error(request, "Security Violation: You cannot delete your own administrative account.")
        log_action(request, 'Self-Deletion Attempt', is_suspicious=True,
                   details='Admin attempted to delete their own account.')
        return redirect('accounts:user_list')
        
    username = user_to_delete.username
    log_action(request, 'Delete User Account', resource='User', resource_id=pk,
               details=f'PERMANENT DELETION of staff account: {username}')
    
    user_to_delete.delete()
    messages.warning(request, f'Staff account for {username} has been permanently deleted.')
    return redirect('accounts:user_list')


import pyotp
import qrcode
import base64
from io import BytesIO

@login_required
def setup_mfa(request):
    user = request.user
    if not user.totp_secret:
        user.totp_secret = pyotp.random_base32()
        user.save()

    # Generate the provisioning URI (the data inside the QR code)
    totp = pyotp.TOTP(user.totp_secret)
    provisioning_uri = totp.provisioning_uri(
        name=user.username,
        issuer_name="Hospital EHR Security"
    )

    # Generate QR Code image
    qr = qrcode.QRCode(version=1, box_size=10, border=5)
    qr.add_data(provisioning_uri)
    qr.make(fit=True)
    img = qr.make_image(fill_color="black", back_color="white")
    
    # Convert image to Base64 string for direct template display
    buffered = BytesIO()
    img.save(buffered, format="PNG")
    qr_code_base64 = base64.b64encode(buffered.getvalue()).decode()

    return render(request, 'accounts/setup_mfa.html', {
        'qr_code': qr_code_base64,
        'secret': user.totp_secret
    })


def verify_mfa(request):
    if not request.user.is_authenticated:
        return redirect('accounts:login')
    
    if request.user.is_locked:
        messages.error(request, 'This account is locked. Please contact an Administrator.')
        return redirect('accounts:logout')
    
    # Smart detection: If user needs to verify but hasn't FINISHED setup yet, send to setup
    if not request.user.totp_secret or not request.user.mfa_enabled:
        return redirect('accounts:setup_mfa')
    
    if request.method == 'POST':
        code = request.POST.get('code')
        user = request.user
        
        # Real TOTP Verification
        if user.totp_secret:
            totp = pyotp.TOTP(user.totp_secret)
            if totp.verify(code):
                request.session['mfa_verified'] = True
                request.session['raac_last_reset'] = timezone.now().isoformat()
                request.session.pop('raac_triggered', None) # Clear flag
                
                # Risk-hysteresis: Reduce risk score by 10 instead of a full wipe
                user.is_locked = False
                user.security_risk_level = max(user.security_risk_level - 10, 10)
                user.failed_login_attempts = 0
                user.save()
                
                log_action(request, 'MFA Verification Success',
                           details=f'Identity verified via Real-time TOTP challenge. Risk reduced to {user.security_risk_level}%.')
                return redirect('accounts:dashboard')
            else:
                user.failed_login_attempts += 1
                attempts_left = 5 - user.failed_login_attempts
                
                if user.failed_login_attempts >= 5:
                    user.is_locked = True
                    details = f'ACCOUNT LOCKED: 5 failed MFA attempts reached for user: {user.username}'
                    messages.error(request, 'Account locked due to too many failed security challenges. Contact Administrator.')
                else:
                    details = f'Failed MFA attempt {user.failed_login_attempts}/5 for user: {user.username}'
                    messages.error(request, f'Invalid security code. {attempts_left} attempt(s) remaining before account lockout.')
                
                user.save()
                log_action(request, 'MFA Verification Failed', is_suspicious=True, details=details)
                
                if user.is_locked:
                    return redirect('accounts:logout')
        else:
            # Fallback for users who haven't set up MFA yet but are forced by RAAC
            messages.warning(request, "Please set up your MFA device first.")
            return redirect('accounts:setup_mfa')
            
    raac_challenge = request.session.get('raac_triggered', False)
    return render(request, 'accounts/verify_mfa.html', {'raac_challenge': raac_challenge})


@login_required
def toggle_mfa(request):
    user = request.user
    if not user.mfa_enabled:
        # If enabling, force them to the setup page first
        return redirect('accounts:setup_mfa')
    
    # Mandatory Policy Enforcement: Only Admins can override MFA requirements
    if not user.is_admin:
        messages.error(request, 'MFA is mandatory for healthcare staff. Contact an Administrator to request changes.')
        return redirect('accounts:dashboard')

    user.mfa_enabled = False
    user.save()
    log_action(request, 'MFA Disabled', details=f'Admin user {user.username} overrode and disabled Multi-Factor Authentication.')
    messages.success(request, 'MFA has been successfully deactivated.')
    return redirect('accounts:dashboard')


@login_required
def confirm_mfa_setup(request):
    """View to finalize MFA setup after scanning QR code."""
    if request.method == 'POST':
        code = request.POST.get('code')
        user = request.user
        totp = pyotp.TOTP(user.totp_secret)
        
        if totp.verify(code):
            user.mfa_enabled = True
            user.save()
            request.session['mfa_verified'] = True
            log_action(request, 'MFA Setup Success', details='New TOTP device registered and verified.')
            messages.success(request, "MFA has been successfully enabled on your account.")
            return redirect('accounts:dashboard')
        else:
            messages.error(request, "Invalid code. Please try scanning the QR code again.")
            
    return redirect('accounts:setup_mfa')


from django.core.paginator import Paginator

@login_required
@admin_required
def audit_log_list(request):
    logs = AuditLog.objects.all().select_related('user').order_by('-timestamp')
    
    # Filtering
    is_suspicious = request.GET.get('suspicious')
    if is_suspicious == '1':
        logs = logs.filter(is_suspicious=True)
    elif is_suspicious == '0':
        logs = logs.filter(is_suspicious=False)
        
    query = request.GET.get('q')
    if query:
        logs = logs.filter(
            Q(action__icontains=query) | 
            Q(details__icontains=query) | 
            Q(user__username__icontains=query)
        )
    
    # Pagination (20 logs per page)
    paginator = Paginator(logs, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    log_action(request, 'View Audit Logs', 
               details=f'Admin reviewed security audit trail. Filtered: {logs.count()} total.')
               
    return render(request, 'accounts/audit_log_list.html', {
        'page_obj': page_obj,
        'is_suspicious': is_suspicious,
        'q': query
    })


@login_required
def global_search(request):
    query = request.GET.get('q', '').strip()
    results = {
        'patients': [],
        'appointments': [],
        'staff': [],
    }
    
    if query:
        # Search Patients
        results['patients'] = Patient.objects.filter(
            Q(first_name__icontains=query) | Q(last_name__icontains=query)
        )[:10]
        
        # Search Appointments
        results['appointments'] = Appointment.objects.filter(
            Q(reason__icontains=query) | Q(notes__icontains=query) | Q(patient__first_name__icontains=query)
        ).select_related('patient')[:10]
        
        # Search Staff (Users)
        if request.user.is_admin:
            results['staff'] = User.objects.filter(
                Q(username__icontains=query) | Q(first_name__icontains=query) | Q(last_name__icontains=query)
            )[:10]

    log_action(request, 'Global Search', details=f'Searched for: "{query}"')
    return render(request, 'accounts/search_results.html', {
        'query': query,
        'results': results
    })


def forgot_password(request):
    if request.user.is_authenticated:
        return redirect('accounts:dashboard')
        
    if request.method == 'POST':
        email = request.POST.get('email', '').strip()
        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            user = None
            
        if user:
            import random
            from datetime import datetime, timedelta
            from django.core.mail import EmailMultiAlternatives
            
            # Generate a secure 6-digit numeric code
            code = f"{secrets.randbelow(900000) + 100000}"
            
            # WIPE ANY PREVIOUS VERIFICATION STATE to prevent bypass vulnerability
            request.session.pop('reset_code_verified', None)
            
            # Save reset context in the user's secure session
            request.session['reset_email'] = email
            request.session['reset_code'] = code
            request.session['reset_code_expiry'] = (datetime.now() + timedelta(minutes=15)).strftime('%Y-%m-%d %H:%M:%S')
            
            subject = "Clinical Access Verification Code - Hospital EHR"
            
            html_content = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <link href="https://fonts.googleapis.com/css2?family=Instrument+Sans:wght@400;600;700&display=swap" rel="stylesheet">
</head>
<body style="font-family: 'Instrument Sans', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif; background-color: #f4f4f5; margin: 0; padding: 40px 20px; color: #18181b;">
    <table width="100%" cellpadding="0" cellspacing="0" border="0" style="background-color: #f4f4f5;">
        <tr>
            <td align="center">
                <table width="100%" max-width="480" cellpadding="0" cellspacing="0" border="0" style="max-width: 480px; background-color: #ffffff; border-radius: 12px; border: 1px solid #e4e4e7; overflow: hidden; box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.05);">
                    <tr>
                        <td style="padding: 40px 40px 20px 40px;">
                            <div style="font-size: 14px; font-weight: 700; color: #4f46e5; text-transform: uppercase; letter-spacing: 1px; margin-bottom: 12px;">
                                ✦ Hospital EHR
                            </div>
                            <h1 style="font-size: 24px; font-weight: 700; color: #09090b; margin: 0 0 16px 0; letter-spacing: -0.5px;">
                                Clinical Access Verification Code
                            </h1>
                            <p style="font-size: 15px; line-height: 24px; color: #52525b; margin: 0 0 32px 0;">
                                We received a request to recover your credentials. Use the 6-digit verification code below to securely authorize your password reset.
                            </p>
                            
                            <div style="background-color: #f8fafc; border: 1px dashed #cbd5e1; border-radius: 8px; padding: 24px; text-align: center; margin-bottom: 32px;">
                                <div style="font-size: 12px; font-weight: 600; color: #64748b; text-transform: uppercase; letter-spacing: 1px; margin-bottom: 8px;">Verification Code</div>
                                <div style="font-size: 36px; font-weight: 700; color: #0f172a; letter-spacing: 8px; font-family: monospace;">{code}</div>
                            </div>
                            
                            <p style="font-size: 13px; line-height: 20px; color: #71717a; margin: 0 0 24px 0; background-color: #f4f4f5; padding: 12px; border-radius: 6px; border-left: 3px solid #4f46e5;">
                                <strong>Security Notice:</strong> This code expires in 15 minutes. If your account has Multi-Factor Authentication (MFA) enabled, your authenticator app token will also be required.
                            </p>
                        </td>
                    </tr>
                    <tr>
                        <td style="background-color: #fafafa; border-top: 1px solid #e4e4e7; padding: 24px 40px; font-size: 12px; line-height: 18px; color: #a1a1aa; text-align: center;">
                            This is an automated transmission. If you did not request this, please ignore it.<br>
                            &copy; 2026 Hospital Electronic Health Record System.
                        </td>
                    </tr>
                </table>
            </td>
        </tr>
    </table>
</body>
</html>"""
            
            text_content = f"Verification Code: {code}"
            
            msg = EmailMultiAlternatives(subject, text_content, 'no-reply@melancompany.com', [email])
            msg.attach_alternative(html_content, "text/html")
            try:
                msg.send()
                log_action(request, 'Password Reset Code Sent', details=f'Verification code sent to: {email}')
            except Exception as e:
                log_action(request, 'Password Reset Mail Failed', is_suspicious=True, details=f'Failed to send to {email}: {str(e)}')
                
        messages.success(request, 'A secure 6-digit verification code has been sent to your registered email.')
        return redirect('accounts:reset_password')
        
    return render(request, 'accounts/forgot_password.html')


def reset_password(request):
    if request.user.is_authenticated:
        return redirect('accounts:dashboard')
        
    email = request.session.get('reset_email')
    session_code = request.session.get('reset_code')
    expiry_str = request.session.get('reset_code_expiry')
    
    if not email or not session_code or not expiry_str:
        messages.error(request, 'No active recovery session found. Please request a new code.')
        return redirect('accounts:forgot_password')
        
    from datetime import datetime
    try:
        expiry = datetime.strptime(expiry_str, '%Y-%m-%d %H:%M:%S')
    except ValueError:
        messages.error(request, 'Invalid recovery session metadata.')
        return redirect('accounts:forgot_password')
        
    if datetime.now() > expiry:
        messages.error(request, 'Your recovery code has expired. Please request a new one.')
        return redirect('accounts:forgot_password')
        
    try:
        user = User.objects.get(email=email)
    except User.DoesNotExist:
        messages.error(request, 'User account not found.')
        return redirect('accounts:forgot_password')
        
    # Check current step
    step = 1
    if request.session.get('reset_code_verified'):
        step = 2
    if request.session.get('reset_password_pending'):
        step = 3
    
    if request.method == 'POST':
        action = request.POST.get('action')
        
        if action == 'verify_code':
            entered_code = request.POST.get('verification_code', '').strip()
            if entered_code == session_code:
                request.session['reset_code_verified'] = True
                step = 2
                return render(request, 'accounts/reset_password.html', {'user_obj': user, 'step': step})
            else:
                messages.error(request, 'Invalid email verification code.')
                return render(request, 'accounts/reset_password.html', {'user_obj': user, 'step': 1})
                
        elif action == 'reset_password':
            if not request.session.get('reset_code_verified'):
                messages.error(request, 'Verification code must be successfully verified first.')
                return redirect('accounts:reset_password')
                
            new_password = request.POST.get('password')
            confirm_password = request.POST.get('confirm_password')
            
            if not new_password or new_password != confirm_password:
                messages.error(request, 'Passwords do not match.')
                return render(request, 'accounts/reset_password.html', {'user_obj': user, 'step': 2})
                
            # Strict Password Security Controls
            if len(new_password) < 8:
                messages.error(request, 'Password must be at least 8 characters long.')
                return render(request, 'accounts/reset_password.html', {'user_obj': user, 'step': 2})
                
            if user.check_password(new_password):
                messages.error(request, 'New password cannot be the same as your old password.')
                return render(request, 'accounts/reset_password.html', {'user_obj': user, 'step': 2})
                
            if new_password.isdigit() or new_password.isalpha():
                messages.error(request, 'Password must contain a mix of letters, numbers, or special characters.')
                return render(request, 'accounts/reset_password.html', {'user_obj': user, 'step': 2})
                
            if new_password.lower() in ['password', 'password123', 'admin123', 'hospital123', 'clinical123']:
                messages.error(request, 'This password is too common and easily guessable. Please choose a stronger password.')
                return render(request, 'accounts/reset_password.html', {'user_obj': user, 'step': 2})
                
            if user.mfa_enabled:
                request.session['reset_password_pending'] = new_password
                step = 3
                return render(request, 'accounts/reset_password.html', {'user_obj': user, 'step': step})
            else:
                try:
                    validate_password(new_password, user=user)
                except ValidationError as e:
                    messages.error(request, e.messages[0])
                    return render(request, 'accounts/reset_password.html', {
        'user_obj': user,
        'step': 2
    })
                
                user.set_password(new_password)
                user.save()
                
                # Wipe session variables securely
                request.session.pop('reset_email', None)
                request.session.pop('reset_code', None)
                request.session.pop('reset_code_expiry', None)
                request.session.pop('reset_code_verified', None)
                
                log_action(request, 'Password Reset Success', details=f'Password securely reset via 2-step verification for user: {user.username}')
                messages.success(request, 'Your password has been securely reset. You can now log in with your new credentials.')
                return redirect('accounts:login')
                
        elif action == 'verify_mfa':
            if not request.session.get('reset_password_pending'):
                messages.error(request, 'Invalid state. Please start the password reset process again.')
                return redirect('accounts:reset_password')
                
            totp_code = request.POST.get('totp_code')
            if not totp_code:
                messages.error(request, 'Multi-Factor Authentication (MFA) verification code is required.')
                return render(request, 'accounts/reset_password.html', {'user_obj': user, 'step': 3})
                
            import pyotp
            totp = pyotp.TOTP(user.totp_secret)
            if not totp.verify(totp_code):
                messages.error(request, 'Invalid Multi-Factor Authentication (MFA) verification code.')
                return render(request, 'accounts/reset_password.html', {'user_obj': user, 'step': 3})
                
            new_password = request.session.get('reset_password_pending')
            try:
                validate_password(new_password, user=user)
            except ValidationError as e:
                messages.error(request, e.messages[0])
                return render(request, 'accounts/reset_password.html', {
                'user_obj': user,
        'step': 2
    })
            user.set_password(new_password)
            user.save()
            
            # Wipe session variables securely
            request.session.pop('reset_email', None)
            request.session.pop('reset_code', None)
            request.session.pop('reset_code_expiry', None)
            request.session.pop('reset_code_verified', None)
            request.session.pop('reset_password_pending', None)
            
            log_action(request, 'Password Reset Success', details=f'Password securely reset via 3-step MFA verification for user: {user.username}')
            messages.success(request, 'Your password has been securely reset. You can now log in with your new credentials.')
            return redirect('accounts:login')
            
    return render(request, 'accounts/reset_password.html', {'user_obj': user, 'step': step})


@login_required
def force_change_password(request):
    from django.contrib.auth.forms import PasswordChangeForm
    
    user = request.user
    if not user.needs_password_change:
        return redirect('accounts:dashboard')

    if request.method == 'POST':
        form = PasswordChangeForm(user, request.POST)
        if form.is_valid():
            saved_user = form.save()
            
            # Clear administrative secrets and release state gates
            saved_user.needs_password_change = False
            saved_user.temp_password = None
            saved_user.save()
            
            # Update session authentication hash to prevent immediate logout
            update_session_auth_hash(request, saved_user)
            
            log_action(request, 'Forced Password Update Completed', resource='User', resource_id=saved_user.id,
                       details=f'User {saved_user.username} completed mandatory onboarding password upgrade.')
            messages.success(request, 'Your temporary password has been upgraded. Please proceed to complete security verification.')
            
            # Forward straight into MFA initialization flow
            return redirect('accounts:setup_mfa')
        else:
            messages.error(request, 'Failed to update credentials. Please address the errors below.')
    else:
        form = PasswordChangeForm(user)
        
    return render(request, 'accounts/force_change_password.html', {
        'form': form,
        'title': 'Secure Account Setup'
    })

