"""
Forms for User Account Management
Professional Django Forms with Validation and Crispy Forms Integration
"""

from django import forms
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm, PasswordChangeForm
from django.contrib.auth import get_user_model
from crispy_forms.helper import FormHelper
from crispy_forms.layout import Layout, Row, Column, Submit, HTML
from crispy_forms.bootstrap import FormActions
import re

User = get_user_model()
from .models import UserPreferences


class CustomUserRegistrationForm(UserCreationForm):
    """
    Enhanced user registration form with additional fields
    """
    first_name = forms.CharField(
        max_length=30,
        required=True,
        widget=forms.TextInput(attrs={
            'placeholder': 'Enter your first name',
            'class': 'form-control'
        })
    )
    last_name = forms.CharField(
        max_length=30,
        required=True,
        widget=forms.TextInput(attrs={
            'placeholder': 'Enter your last name',
            'class': 'form-control'
        })
    )
    email = forms.EmailField(
        required=True,
        widget=forms.EmailInput(attrs={
            'placeholder': 'Enter your email address',
            'class': 'form-control'
        })
    )
    phone_number = forms.CharField(
        max_length=15,
        required=False,
        widget=forms.TextInput(attrs={
            'placeholder': '+91 1234567890',
            'class': 'form-control'
        })
    )
    
    class Meta:
        model = User
        fields = ('username', 'first_name', 'last_name', 'email', 'phone_number', 'password1', 'password2')
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_method = 'post'
        self.helper.form_class = 'form-horizontal'
        self.helper.label_class = 'col-md-3'
        self.helper.field_class = 'col-md-9'
        
        # Customize field appearance
        self.fields['username'].widget.attrs.update({
            'placeholder': 'Choose a unique username',
            'class': 'form-control'
        })
        self.fields['password1'].widget.attrs.update({
            'placeholder': 'Enter a strong password',
            'class': 'form-control'
        })
        self.fields['password2'].widget.attrs.update({
            'placeholder': 'Confirm your password',
            'class': 'form-control'
        })
        
        self.helper.layout = Layout(
            Row(
                Column('first_name', css_class='col-md-6'),
                Column('last_name', css_class='col-md-6'),
            ),
            'username',
            'email',
            'phone_number',
            Row(
                Column('password1', css_class='col-md-6'),
                Column('password2', css_class='col-md-6'),
            ),
            HTML('<hr>'),
            FormActions(
                Submit('register', 'Create Account', css_class='btn btn-primary btn-lg'),
                HTML('<a href="{% url "accounts:login" %}" class="btn btn-link">Already have an account?</a>')
            )
        )
    
    def clean_email(self):
        email = self.cleaned_data['email']
        if User.objects.filter(email=email).exists():
            raise forms.ValidationError("This email address is already registered.")
        return email
    
    def clean_phone_number(self):
        phone = self.cleaned_data.get('phone_number')
        if phone:
            # Simple phone validation
            phone_pattern = re.compile(r'^\+?[\d\s\-\(\)]+$')
            if not phone_pattern.match(phone):
                raise forms.ValidationError("Please enter a valid phone number.")
        return phone
    
    def save(self, commit=True):
        user = super().save(commit=False)
        user.email = self.cleaned_data['email']
        user.first_name = self.cleaned_data['first_name']
        user.last_name = self.cleaned_data['last_name']
        user.phone_number = self.cleaned_data.get('phone_number')
        
        if commit:
            user.save()
        return user


class UserPreferencesForm(forms.ModelForm):
    """Form for user travel preferences"""
    
    class Meta:
        model = UserPreferences
        fields = [
            'preferred_currency', 
            'preferred_language', 
            'newsletter_subscription',
            'sms_notifications',
            'email_notifications'
        ]
        widgets = {
            'preferred_currency': forms.Select(attrs={
                'class': 'form-select',
            }),
            'preferred_language': forms.Select(attrs={
                'class': 'form-select',
            }),
            'newsletter_subscription': forms.CheckboxInput(attrs={
                'class': 'form-check-input',
            }),
            'sms_notifications': forms.CheckboxInput(attrs={
                'class': 'form-check-input',
            }),
            'email_notifications': forms.CheckboxInput(attrs={
                'class': 'form-check-input',
            }),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['preferred_currency'].required = False
        self.fields['preferred_language'].required = False


class CustomAuthenticationForm(AuthenticationForm):
    """
    Enhanced login form with crispy forms styling
    """
    username = forms.CharField(
        widget=forms.TextInput(attrs={
            'placeholder': 'Username or Email',
            'class': 'form-control',
            'autofocus': True
        })
    )
    password = forms.CharField(
        widget=forms.PasswordInput(attrs={
            'placeholder': 'Enter your password',
            'class': 'form-control'
        })
    )
    remember_me = forms.BooleanField(
        required=False,
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'})
    )
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_method = 'post'
        self.helper.form_class = 'form-signin'
        
        self.helper.layout = Layout(
            'username',
            'password',
            'remember_me',
            HTML('<hr>'),
            FormActions(
                Submit('login', 'Sign In', css_class='btn btn-primary btn-lg btn-block'),
                HTML('<a href="{% url "accounts:register" %}" class="btn btn-link">Create New Account</a>')
            )
        )


class UserProfileForm(forms.ModelForm):
    """
    Form for updating user profile information
    """
    date_of_birth = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={
            'type': 'date',
            'class': 'form-control'
        })
    )
    
    class Meta:
        model = User
        fields = [
            'first_name', 'last_name', 'email', 'phone_number',
            'date_of_birth', 'profile_picture', 'address',
            'city', 'state', 'country', 'postal_code'
        ]
        widgets = {
            'first_name': forms.TextInput(attrs={'class': 'form-control'}),
            'last_name': forms.TextInput(attrs={'class': 'form-control'}),
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
            'phone_number': forms.TextInput(attrs={'class': 'form-control'}),
            'address': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'city': forms.TextInput(attrs={'class': 'form-control'}),
            'state': forms.TextInput(attrs={'class': 'form-control'}),
            'country': forms.TextInput(attrs={'class': 'form-control'}),
            'postal_code': forms.TextInput(attrs={'class': 'form-control'}),
            'profile_picture': forms.FileInput(attrs={'class': 'form-control'}),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_method = 'post'
        self.helper.form_enctype = 'multipart/form-data'
        
        self.helper.layout = Layout(
            HTML('<h4>Personal Information</h4><hr>'),
            Row(
                Column('first_name', css_class='col-md-6'),
                Column('last_name', css_class='col-md-6'),
            ),
            Row(
                Column('email', css_class='col-md-8'),
                Column('phone_number', css_class='col-md-4'),
            ),
            Row(
                Column('date_of_birth', css_class='col-md-6'),
                Column('profile_picture', css_class='col-md-6'),
            ),
            HTML('<h4>Address Information</h4><hr>'),
            'address',
            Row(
                Column('city', css_class='col-md-4'),
                Column('state', css_class='col-md-4'),
                Column('postal_code', css_class='col-md-4'),
            ),
            'country',
            HTML('<hr>'),
            FormActions(
                Submit('update', 'Update Profile', css_class='btn btn-primary'),
                HTML('<a href="{% url "accounts:profile" %}" class="btn btn-secondary">Cancel</a>')
            )
        )
    
    def clean_email(self):
        email = self.cleaned_data['email']
        if User.objects.filter(email=email).exclude(pk=self.instance.pk).exists():
            raise forms.ValidationError("This email address is already in use.")
        return email


class CustomPasswordChangeForm(PasswordChangeForm):
    """
    Enhanced password change form with crispy forms styling
    """
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_method = 'post'
        
        # Update field widgets
        self.fields['old_password'].widget.attrs.update({
            'class': 'form-control',
            'placeholder': 'Enter current password'
        })
        self.fields['new_password1'].widget.attrs.update({
            'class': 'form-control',
            'placeholder': 'Enter new password'
        })
        self.fields['new_password2'].widget.attrs.update({
            'class': 'form-control',
            'placeholder': 'Confirm new password'
        })
        
        self.helper.layout = Layout(
            'old_password',
            'new_password1',
            'new_password2',
            HTML('<hr>'),
            FormActions(
                Submit('change_password', 'Change Password', css_class='btn btn-primary'),
                HTML('<a href="{% url "accounts:profile" %}" class="btn btn-secondary">Cancel</a>')
            )
        )