from django import forms
from .models import Appointment
from accounts.models import User


class AppointmentForm(forms.ModelForm):
    class Meta:
        model = Appointment
        fields = ['patient', 'doctor', 'date', 'time', 'reason', 'notes']
        widgets = {
            'patient': forms.Select(attrs={'class': 'form-select'}),
            'doctor': forms.Select(attrs={'class': 'form-select'}),
            'date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'time': forms.TimeInput(attrs={'class': 'form-control', 'type': 'time'}),
            'reason': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'notes': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.fields['patient'].required = True
        self.fields['doctor'].required = True
        self.fields['date'].required = True
        self.fields['time'].required = True
        self.fields['reason'].required = True
        self.fields['notes'].required = False

        self.fields['doctor'].queryset = User.objects.filter(role='doctor', is_active=True)


class AppointmentStatusForm(forms.ModelForm):
    class Meta:
        model = Appointment
        fields = ['status', 'notes']
        widgets = {
            'status': forms.Select(attrs={'class': 'form-select'}),
            'notes': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }

    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        
        # Enforce Role-Based Lifecycle Limits
        if user:
            current_val = self.instance.status

            # Build permissible option pool
            if user.role == 'receptionist':
                options = [('scheduled', 'Scheduled'), ('cancelled', 'Cancelled')]
            elif user.role == 'nurse':
                options = [('checked_in', 'Checked In'), ('in_progress', 'In Progress')]
            elif user.role == 'doctor':
                options = [('completed', 'Completed'), ('follow_up', 'Next Appointment Needed')]
            else:
                # Admin gets everything
                options = list(self.fields['status'].choices)

            # Ensure existing status is in the list so we don't accidentally destroy state
            current_choice = next((c for c in self.fields['status'].choices if c[0] == current_val), None)
            if current_choice and current_choice not in options:
                options.insert(0, current_choice)
            
            self.fields['status'].choices = options