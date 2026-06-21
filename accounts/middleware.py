import re
from django.shortcuts import redirect
from django.urls import reverse
from django.contrib import messages
from django.utils import timezone
from datetime import timedelta
from .models import AuditLog


class RiskAwareMiddleware:
    """
    Centralized Risk-Aware Access Control (RAAC) engine.
    Monitors all user activity across the entire system and enforces
    step-up authentication when anomalous behavioral patterns are detected.

    Threat Classification (strict priority):
      1. Data Harvesting   - Accessing many different patient records
      2. Data Scraping     - Repeatedly accessing sensitive clinical data
      3. Admin Probing     - Rapid access to admin/security panels
      4. Record Tampering  - Rapid create/edit/delete operations
      5. Navigation Flood  - General abnormal navigation velocity
    """

    # Action categories used for threat classification
    SENSITIVE_READ_ACTIONS = [
        'View Patient Detail',
        'View Clinical Records',
        'View Appointment Detail',
    ]

    SENSITIVE_LIST_ACTIONS = [
        'View Patient List',
        'View Clinical Patient List',
        'View Appointment List',
    ]

    ADMIN_ACTIONS = [
        'View User Management',
        'View Audit Logs',
        'Create User Account',
        'Edit User Account',
    ]

    WRITE_ACTIONS = [
        'Create Patient',
        'Edit Patient Record',
        'Toggle Patient Status',
        'Add Clinical Note',
        'Add Diagnosis',
        'Add Prescription',
        'Record Vital Signs',
        'Create Appointment',
        'Edit Appointment',
        'Update Appointment Status',
    ]

    ALL_SENSITIVE = SENSITIVE_READ_ACTIONS + SENSITIVE_LIST_ACTIONS + ADMIN_ACTIONS + WRITE_ACTIONS

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if not request.user.is_authenticated:
            return self.get_response(request)

        user = request.user
        excluded_paths = [
            reverse('accounts:verify_mfa'),
            reverse('accounts:setup_mfa'),
            reverse('accounts:confirm_mfa_setup'),
            reverse('accounts:logout'),
            reverse('accounts:login'),
            reverse('accounts:force_change_password'),
        ]
        is_excluded = (
            request.path in excluded_paths
            or request.path.startswith('/static/')
            or request.path.startswith('/media/')
            or 'favicon' in request.path
        )

        if not is_excluded:
            self._run_raac_scan(request, user)

        # ─── TIER 1 GATING: COMPULSORY FIRST-LOGIN CREDENTIAL UPGRADE ───
        if user.needs_password_change:
            change_path = reverse('accounts:force_change_password')
            if request.path != change_path and not is_excluded:
                messages.info(request, 'First-login detected. Establish custom credentials to proceed.')
                return redirect('accounts:force_change_password')

        # Strict Enforcement: ALL authenticated users MUST maintain an active verified session
        is_verified = request.session.get('mfa_verified', False)

        if not is_verified and not user.mfa_exempt:
            if not is_excluded:
                messages.warning(request, 'Please complete security verification to access portal features.')
                return redirect('accounts:verify_mfa')

        return self.get_response(request)

    def _get_window_start(self, request):
        """Determine the RAAC analysis window start time."""
        window_start = timezone.now() - timedelta(minutes=2)
        last_reset = request.session.get('raac_last_reset')
        if last_reset and isinstance(last_reset, str):
            from django.utils.dateparse import parse_datetime
            parsed = parse_datetime(last_reset)
            if parsed and parsed > window_start:
                window_start = parsed
        return window_start

    def _run_raac_scan(self, request, user):
        """
        Analyzes recent activity and classifies threats.
        Uses view-level log_action entries (not middleware-generated entries).
        """
        window_start = self._get_window_start(request)

        # Pull all user logs in the window, excluding RAAC alerts and MFA events
        recent_logs = AuditLog.objects.filter(
            user=user,
            timestamp__gt=window_start,
        ).exclude(
            action__startswith='RAAC Alert'
        ).exclude(
            action__startswith='MFA'
        )

        total_actions = recent_logs.count()

        # Sensitive data reads (patient detail / clinical records)
        sensitive_reads = recent_logs.filter(action__in=self.SENSITIVE_READ_ACTIONS)
        total_sensitive_reads = sensitive_reads.count()
        distinct_records = sensitive_reads.values('resource_id').distinct().count()

        # Admin panel access
        admin_access = recent_logs.filter(action__in=self.ADMIN_ACTIONS).count()

        # Write operations
        write_ops = recent_logs.filter(action__in=self.WRITE_ACTIONS).count()

        # Classify threat (strict priority)
        threat = None

        if distinct_records > 4:
            threat = self._alert_harvesting(user, sensitive_reads, distinct_records)
        elif total_sensitive_reads > 20:
            threat = self._alert_scraping(user, sensitive_reads, total_sensitive_reads, distinct_records)
        elif admin_access > 15:
            threat = self._alert_admin_probing(user, admin_access)
        elif write_ops > 10:
            threat = self._alert_tampering(user, recent_logs, write_ops)
        elif total_actions > 40:
            threat = self._alert_flood(user, total_actions)

        if threat:
            user.security_risk_level = min(user.security_risk_level + 25, 100)
            if user.security_risk_level >= 70:
                user.is_locked = True
            user.save()
            if user.security_risk_level > 40:
                request.session['mfa_verified'] = False
                request.session['raac_triggered'] = True

            AuditLog.objects.create(
                user=user,
                action=f"RAAC Alert: {threat['reason']}",
                details=threat['details'],
                is_suspicious=True,
                ip_address=request.META.get('REMOTE_ADDR'),
            )

    def _get_patient_names(self, sensitive_logs):
        """Look up patient names from resource_ids in logs."""
        from patients.models import Patient
        ids = list(sensitive_logs.values_list('resource_id', flat=True).distinct())
        ids = [i for i in ids if i is not None]
        if not ids:
            return 'Unknown'
        patients = Patient.objects.filter(id__in=ids)
        return ", ".join(f"{p.first_name} {p.last_name}" for p in patients)

    def _alert_harvesting(self, user, sensitive_logs, distinct_records):
        names = self._get_patient_names(sensitive_logs)
        risk = min(user.security_risk_level + 25, 100)
        return {
            'reason': 'Data Harvesting',
            'details': (
                f"CRITICAL: Multi-record data exfiltration pattern detected. "
                f"{distinct_records} unique patient profiles accessed in rapid succession. "
                f"Targeted profiles: [{names}]. "
                f"This pattern is consistent with unauthorized bulk data access or insider threat behavior. "
                f"Step-up MFA enforced. Risk level elevated to {risk}%."
            ),
        }

    def _alert_scraping(self, user, sensitive_logs, total_reads, distinct_records):
        names = self._get_patient_names(sensitive_logs)
        risk = min(user.security_risk_level + 25, 100)
        return {
            'reason': 'Data Scraping',
            'details': (
                f"HIGH: Repetitive data scraping pattern detected. "
                f"{total_reads} sensitive record views in rapid succession "
                f"targeting {distinct_records} patient profile(s): [{names}]. "
                f"This is consistent with automated bot activity or screen-scraping tools. "
                f"Step-up MFA enforced. Risk level elevated to {risk}%."
            ),
        }

    def _alert_admin_probing(self, user, admin_count):
        risk = min(user.security_risk_level + 25, 100)
        return {
            'reason': 'Privilege Probing',
            'details': (
                f"HIGH: Excessive admin panel access detected. "
                f"{admin_count} administrative actions performed in rapid succession "
                f"including user management and audit log review. "
                f"This may indicate privilege escalation reconnaissance or unauthorized access. "
                f"Step-up MFA enforced. Risk level elevated to {risk}%."
            ),
        }

    def _alert_tampering(self, user, recent_logs, write_count):
        actions = list(
            recent_logs.filter(action__in=self.WRITE_ACTIONS)
            .values_list('action', flat=True)[:5]
        )
        action_summary = ", ".join(actions)
        risk = min(user.security_risk_level + 25, 100)
        return {
            'reason': 'Record Tampering',
            'details': (
                f"HIGH: Abnormal write-operation velocity detected. "
                f"{write_count} record modifications in rapid succession. "
                f"Recent operations: [{action_summary}]. "
                f"This may indicate automated data injection or unauthorized mass record alteration. "
                f"Step-up MFA enforced. Risk level elevated to {risk}%."
            ),
        }

    def _alert_flood(self, user, total_actions):
        risk = min(user.security_risk_level + 25, 100)
        return {
            'reason': 'Navigation Flood',
            'details': (
                f"MEDIUM: Abnormal navigation velocity detected. "
                f"{total_actions} page transitions in under 2 minutes. "
                f"This exceeds normal human interaction patterns and may indicate "
                f"session hijacking or automated reconnaissance. "
                f"Step-up MFA enforced. Risk level elevated to {risk}%."
            ),
        }
