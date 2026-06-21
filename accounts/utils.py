from .models import AuditLog, User
from django.utils import timezone
from datetime import timedelta

def log_action(request, action, resource='', resource_id=None, is_suspicious=False, details=''):
    """
    Utility to record security events and user actions.
    This is now a pure logging tool; Enforcement is handled by RiskAwareMiddleware.
    """
    user = request.user if request.user.is_authenticated else None
    
    # Get IP address
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0]
    else:
        ip = request.META.get('REMOTE_ADDR')
        
    AuditLog.objects.create(
        user=user,
        action=action,
        resource=resource,
        resource_id=resource_id,
        ip_address=ip,
        is_suspicious=is_suspicious,
        details=details
    )
