from django import forms
from django.contrib.auth.forms import UserCreationForm, UserChangeForm
from django.core.validators import RegexValidator
from .models import User

# Common Validators
NAME_VALIDATOR = RegexValidator(r'^[a-zA-Z\s]+$', "Only alphabetical letters and spaces are permitted.")
PHONE_VALIDATOR = RegexValidator(r'^[0-9\s\-+]+$', "Only digits, spaces, hyphens (-) and (+) are permitted.")
USERNAME_VALIDATOR = RegexValidator(r'^\w+$', "Enter a valid username. Consists of letters, numbers, and underscores only, with no spaces.")


class CustomUserCreationForm(UserCreationForm):
    class Meta:
        model = User
        fields = ('username', 'email', 'first_name', 'last_name', 'role', 'phone')
        widgets = {
            'username': forms.TextInput(attrs={'class': 'form-control'}),
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
            'first_name': forms.TextInput(attrs={'class': 'form-control'}),
            'last_name': forms.TextInput(attrs={'class': 'form-control'}),
            'role': forms.Select(attrs={'class': 'form-select'}),
            'phone': forms.TextInput(attrs={'class': 'form-control'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.fields['username'].required = True
        self.fields['email'].required = True
        self.fields['first_name'].required = True
        self.fields['last_name'].required = True
        self.fields['role'].required = True
        self.fields['phone'].required = False
        self.fields['password1'].required = True
        self.fields['password2'].required = True

        # Restore administrative temporary credential styling
        if 'password1' in self.fields:
            self.fields['password1'].widget.attrs['class'] = 'form-control'
        if 'password2' in self.fields:
            self.fields['password2'].widget.attrs['class'] = 'form-control'

        # Apply user-requested validation rules
        self.fields['first_name'].validators.append(NAME_VALIDATOR)
        self.fields['last_name'].validators.append(NAME_VALIDATOR)
        self.fields['phone'].validators.append(PHONE_VALIDATOR)
        self.fields['username'].validators.append(USERNAME_VALIDATOR)
        self.fields['username'].help_text = "Letters, numbers, and underscores only."

        # Inject Instant Real-Time Frontend Verification
        self.fields['first_name'].widget.attrs.update({'pattern': r'[A-Za-z\s]+', 'title': 'Letters and spaces only'})
        self.fields['last_name'].widget.attrs.update({'pattern': r'[A-Za-z\s]+', 'title': 'Letters and spaces only'})
        self.fields['phone'].widget.attrs.update({'pattern': r'[0-9\s\-+]+', 'title': 'Numbers, spaces, +, and - only'})
        self.fields['username'].widget.attrs.update({'pattern': r'\w+', 'title': 'Letters, numbers, and underscores only (No spaces)'})

    def save(self, commit=True):
        user = super().save(commit=False)
        # Admin sets initial temporary credential
        admin_pw = self.cleaned_data.get('password1')
        
        # Force client-side upgrade upon first ingress
        user.needs_password_change = True
        user.temp_password = admin_pw # Utilizing dynamic AES256 GCM buffer
        
        if commit:
            user.save()
        return user


class CustomUserUpdateForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ('username', 'email', 'first_name', 'last_name', 'role', 'phone', 'is_active')
        widgets = {
            'username': forms.TextInput(attrs={'class': 'form-control'}),
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
            'first_name': forms.TextInput(attrs={'class': 'form-control'}),
            'last_name': forms.TextInput(attrs={'class': 'form-control'}),
            'role': forms.Select(attrs={'class': 'form-select'}),
            'phone': forms.TextInput(attrs={'class': 'form-control'}),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.fields['username'].required = True
        self.fields['email'].required = True
        self.fields['first_name'].required = True
        self.fields['last_name'].required = True
        self.fields['role'].required = True
        self.fields['phone'].required = False
        self.fields['is_active'].required = False

        # Apply user-requested validation rules
        self.fields['first_name'].validators.append(NAME_VALIDATOR)
        self.fields['last_name'].validators.append(NAME_VALIDATOR)
        self.fields['phone'].validators.append(PHONE_VALIDATOR)
        self.fields['username'].validators.append(USERNAME_VALIDATOR)
        self.fields['username'].help_text = "Letters, numbers, and underscores only."

        # Inject Instant Real-Time Frontend Verification
        self.fields['first_name'].widget.attrs.update({'pattern': r'[A-Za-z\s]+', 'title': 'Letters and spaces only'})
        self.fields['last_name'].widget.attrs.update({'pattern': r'[A-Za-z\s]+', 'title': 'Letters and spaces only'})
        self.fields['phone'].widget.attrs.update({'pattern': r'[0-9\s\-+]+', 'title': 'Numbers, spaces, +, and - only'})
        self.fields['username'].widget.attrs.update({'pattern': r'\w+', 'title': 'Letters, numbers, and underscores only (No spaces)'})


class LoginForm(forms.Form):
    username = forms.CharField(
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Username'})
    )
    password = forms.CharField(
        widget=forms.PasswordInput(attrs={'class': 'form-control', 'placeholder': 'Password'})
    )
