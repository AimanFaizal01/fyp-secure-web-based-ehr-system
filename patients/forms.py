from django import forms
from .models import Patient


from django.core.validators import RegexValidator

# Common Validators
NAME_VALIDATOR = RegexValidator(r'^[a-zA-Z\s]+$', "Only alphabetical letters and spaces are permitted.")
PHONE_VALIDATOR = RegexValidator(r'^[0-9\s\-+]+$', "Only digits, spaces, hyphens (-) and (+) are permitted.")

class PatientForm(forms.ModelForm):
    class Meta:
        model = Patient
        fields = [
            'first_name', 'last_name', 'date_of_birth', 'gender',
            'phone', 'email', 'address', 'emergency_contact_name',
            'emergency_contact_phone'
        ]
        widgets = {
            'first_name': forms.TextInput(attrs={'class': 'form-control'}),
            'last_name': forms.TextInput(attrs={'class': 'form-control'}),
            'date_of_birth': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'gender': forms.Select(attrs={'class': 'form-select'}),
            'phone': forms.TextInput(attrs={'class': 'form-control'}),
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
            'address': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'emergency_contact_name': forms.TextInput(attrs={'class': 'form-control'}),
            'emergency_contact_phone': forms.TextInput(attrs={'class': 'form-control'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        self.fields['first_name'].required = True
        self.fields['last_name'].required = True
        self.fields['date_of_birth'].required = True
        self.fields['gender'].required = True
        self.fields['phone'].required = True
        self.fields['address'].required = True

        self.fields['email'].required = False
        self.fields['emergency_contact_name'].required = False
        self.fields['emergency_contact_phone'].required = False
        # Apply user-requested consistency rules
        self.fields['first_name'].validators.append(NAME_VALIDATOR)
        self.fields['last_name'].validators.append(NAME_VALIDATOR)
        self.fields['phone'].validators.append(PHONE_VALIDATOR)
        self.fields['emergency_contact_name'].validators.append(NAME_VALIDATOR)
        self.fields['emergency_contact_phone'].validators.append(PHONE_VALIDATOR)

        # Inject Instant Real-Time Frontend Verification
        self.fields['first_name'].widget.attrs.update({'pattern': r'[A-Za-z\s]+', 'title': 'Letters and spaces only'})
        self.fields['last_name'].widget.attrs.update({'pattern': r'[A-Za-z\s]+', 'title': 'Letters and spaces only'})
        self.fields['phone'].widget.attrs.update({'pattern': r'[0-9\s\-+]+', 'title': 'Numbers, spaces, +, and - only'})
        self.fields['emergency_contact_name'].widget.attrs.update({'pattern': r'[A-Za-z\s]+', 'title': 'Letters and spaces only'})
        self.fields['emergency_contact_phone'].widget.attrs.update({'pattern': r'[0-9\s\-+]+', 'title': 'Numbers, spaces, +, and - only'})

        # Date constraint: Clamp maximum selection to today's timestamp
        from django.utils import timezone
        today = timezone.now().date().isoformat()
        self.fields['date_of_birth'].widget.attrs.update({'max': today, 'title': 'Date of birth cannot be in the future'})

    def clean_date_of_birth(self):
        from django.utils import timezone
        dob = self.cleaned_data.get('date_of_birth')
        if dob and dob > timezone.now().date():
            raise forms.ValidationError("Date of birth cannot be set in the future.")
        return dob
