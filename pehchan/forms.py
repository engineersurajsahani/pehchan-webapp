from django import forms
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from django.contrib.auth.models import User
from .models import EventVolunteer, LifetimeVolunteer, MaterialDonation, MoneyDonation, ContactMessage, AnonymousDonation
import re


def validate_indian_mobile_number(number):
    """Enforce valid 10-digit mobile number starting with 6, 7, 8, or 9 and reject sequential/dummy numbers"""
    number = str(number).strip()
    if not re.match(r'^[6-9]\d{9}$', number):
        raise forms.ValidationError("Please enter a valid 10-digit Indian mobile number starting with 6, 7, 8, or 9.")
    
    # Reject dummy repetitive numbers like 9999999999, 8888888888, 7777777777
    if len(set(number)) == 1:
        raise forms.ValidationError("Please enter a valid mobile number, not a repeating digit pattern.")
        
    # Reject common fake test sequences
    fake_sequences = ['1234567890', '9876543210', '9898989898', '9900990099', '9123456789']
    if number in fake_sequences:
        raise forms.ValidationError("Please enter your actual valid mobile number.")
    return number


class SignUpForm(UserCreationForm):
    email = forms.EmailField(required=True, widget=forms.EmailInput(attrs={
        'class': 'form-control',
        'placeholder': 'Email'
    }))
    first_name = forms.CharField(max_length=100, required=True, widget=forms.TextInput(attrs={
        'class': 'form-control',
        'placeholder': 'First Name'
    }))
    last_name = forms.CharField(max_length=100, required=True, widget=forms.TextInput(attrs={
        'class': 'form-control',
        'placeholder': 'Last Name'
    }))
    
    class Meta:
        model = User
        fields = ['username', 'email', 'first_name', 'last_name', 'password1', 'password2']
        widgets = {
            'username': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Username'
            }),
        }
    
    def __init__(self, *args, **kwargs):
        super(SignUpForm, self).__init__(*args, **kwargs)
        self.fields['password1'].widget.attrs.update({'class': 'form-control', 'placeholder': 'Password'})
        self.fields['password2'].widget.attrs.update({'class': 'form-control', 'placeholder': 'Confirm Password'})

    def clean_email(self):
        email = self.cleaned_data.get('email', '').strip().lower()
        if not email:
            raise forms.ValidationError("Email is required.")
        # Reject disposable / fake domains
        fake_domains = ['tempmail.com', 'mailinator.com', '10minutemail.com', 'throwawaymail.com', 'fake.com', 'test.com']
        domain = email.split('@')[-1] if '@' in email else ''
        if domain in fake_domains:
            raise forms.ValidationError("Disposable or fake email addresses are not allowed. Please enter a valid email.")
        if User.objects.filter(email__iexact=email).exists():
            raise forms.ValidationError("An account with this email address already exists.")
        return email

    def clean_first_name(self):
        first_name = self.cleaned_data.get('first_name', '').strip()
        if len(first_name) < 2 or not first_name.replace(' ', '').isalpha():
            raise forms.ValidationError("First name must contain at least 2 alphabetic characters.")
        return first_name

    def clean_last_name(self):
        last_name = self.cleaned_data.get('last_name', '').strip()
        if len(last_name) < 2 or not last_name.replace(' ', '').isalpha():
            raise forms.ValidationError("Last name must contain at least 2 alphabetic characters.")
        return last_name


class LoginForm(AuthenticationForm):
    username = forms.CharField(widget=forms.TextInput(attrs={
        'class': 'form-control',
        'placeholder': 'Username'
    }))
    password = forms.CharField(widget=forms.PasswordInput(attrs={
        'class': 'form-control',
        'placeholder': 'Password'
    }))


class EventVolunteerForm(forms.ModelForm):
    contact_number = forms.CharField(
        max_length=10,
        min_length=10,
        required=True,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Contact Number (10 digits)',
            'pattern': '[0-9]{10}',
            'title': 'Please enter exactly 10 digits'
        })
    )
    
    class Meta:
        model = EventVolunteer
        fields = ['contact_number']
    
    def clean_contact_number(self):
        contact_number = self.cleaned_data.get('contact_number')
        return validate_indian_mobile_number(contact_number)
        

class LifetimeVolunteerForm(forms.ModelForm):
    contact_number = forms.CharField(
        max_length=10,
        min_length=10,
        required=True,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Contact Number (10 digits)',
            'pattern': '[0-9]{10}',
            'title': 'Please enter exactly 10 digits'
        })
    )
    
    class Meta:
        model = LifetimeVolunteer
        fields = ['contact_number', 'motivation']
        widgets = {
            'motivation': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 5,
                'placeholder': 'Tell us why you want to become a lifetime volunteer...'
            }),
        }
    
    def clean_contact_number(self):
        contact_number = self.cleaned_data.get('contact_number')
        return validate_indian_mobile_number(contact_number)


class MaterialDonationForm(forms.ModelForm):
    contact_number = forms.CharField(
        max_length=10,
        min_length=10,
        required=True,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Contact Number (10 digits)',
            'pattern': '[0-9]{10}',
            'title': 'Please enter exactly 10 digits'
        })
    )
    
    class Meta:
        model = MaterialDonation
        fields = ['item_name', 'quantity', 'location', 'contact_number', 'message']
        widgets = {
            'item_name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Item Name'
            }),
            'quantity': forms.NumberInput(attrs={
                'class': 'form-control',
                'placeholder': 'Quantity',
                'min': 1
            }),
            'location': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Your Location'
            }),
            'message': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Additional message (optional)'
            }),
        }
    
    def clean_contact_number(self):
        contact_number = self.cleaned_data.get('contact_number')
        return validate_indian_mobile_number(contact_number)


class MoneyDonationForm(forms.ModelForm):
    receipt_upload = forms.FileField(
        required=True,
        widget=forms.FileInput(attrs={
            'class': 'form-control',
            'accept': 'image/*,.pdf'
        })
    )
    
    contact_number = forms.CharField(
        max_length=10,
        min_length=10,
        required=True,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Contact Number (10 digits)',
            'pattern': '[0-9]{10}',
            'title': 'Please enter exactly 10 digits'
        })
    )

    class Meta:
        model = MoneyDonation
        fields = ['amount', 'contact_number', 'receipt_upload']
        widgets = {
            'amount': forms.NumberInput(attrs={
                'class': 'form-control',
                'placeholder': 'Amount in ₹',
                'min': 1,
                'step': '0.01'
            }),
        }
    
    def clean_contact_number(self):
        contact_number = self.cleaned_data.get('contact_number')
        return validate_indian_mobile_number(contact_number)


class CertificateVerificationForm(forms.Form):
    certificate_id = forms.CharField(
        max_length=100,
        required=True,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'id': 'certificate_id',  # Explicitly set the ID
            'placeholder': 'Enter Certificate ID (e.g. VOL-2024-001)'
        })
    )


class ContactMessageForm(forms.ModelForm):
    """Form for contact messages from home page"""
    class Meta:
        model = ContactMessage
        fields = ['name', 'email', 'message']
        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Name',
                'required': True
            }),
            'email': forms.EmailInput(attrs={
                'class': 'form-control',
                'placeholder': 'Email',
                'required': True
            }),
            'message': forms.Textarea(attrs={
                'class': 'form-control',
                'placeholder': 'Message',
                'rows': 5,
                'required': True
            }),
        }
        labels = {
            'name': 'Your Name',
            'email': 'Your Email',
            'message': 'Your Message'
        }


class AnonymousDonationForm(forms.ModelForm):
    """Form for anonymous donations"""
    class Meta:
        model = AnonymousDonation
        fields = ['donor_name', 'donor_email', 'donor_phone', 'amount', 'transaction_id', 'receipt', 'wants_receipt', 'message']
        widgets = {
            'donor_name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Your Name (Optional)',
            }),
            'donor_email': forms.EmailInput(attrs={
                'class': 'form-control',
                'placeholder': 'Email (Optional - for receipt)',
            }),
            'donor_phone': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Phone Number (Optional)',
            }),
            'amount': forms.NumberInput(attrs={
                'class': 'form-control',
                'placeholder': 'Amount Donated (₹)',
                'min': 1,
                'step': '0.01',
                'required': True
            }),
            'transaction_id': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'UPI Transaction ID (Optional)',
            }),
            'receipt': forms.FileInput(attrs={
                'class': 'form-control',
                'accept': 'image/*,.pdf'
            }),
            'wants_receipt': forms.CheckboxInput(attrs={
                'class': 'form-check-input',
            }),
            'message': forms.Textarea(attrs={
                'class': 'form-control',
                'placeholder': 'Message (Optional)',
                'rows': 3,
            }),
        }
        labels = {
            'donor_name': 'Name',
            'donor_email': 'Email',
            'donor_phone': 'Phone',
            'amount': 'Donation Amount',
            'transaction_id': 'Transaction ID',
            'receipt': 'Payment Receipt',
            'wants_receipt': 'I want a receipt marked as "Anonymous"',
            'message': 'Message'
        }

    def clean_donor_email(self):
        email = self.cleaned_data.get('donor_email')
        if email:
            email = email.strip().lower()
            fake_domains = ['tempmail.com', 'mailinator.com', '10minutemail.com', 'throwawaymail.com', 'fake.com', 'test.com']
            domain = email.split('@')[-1] if '@' in email else ''
            if domain in fake_domains:
                raise forms.ValidationError("Please provide a valid non-disposable email address.")
        return email

    def clean_donor_phone(self):
        phone = self.cleaned_data.get('donor_phone')
        if phone:
            return validate_indian_mobile_number(phone)
        return phone


class ForgotPasswordForm(forms.Form):
    """Form for entering email to reset password"""
    email = forms.EmailField(
        widget=forms.EmailInput(attrs={
            'class': 'form-control',
            'placeholder': 'Enter your email address',
            'required': True
        })
    )


class OTPVerificationForm(forms.Form):
    """Form for entering OTP"""
    otp = forms.CharField(
        max_length=6,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Enter 6-digit OTP',
            'required': True
        })
    )


from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError as DjangoValidationError


class ResetPasswordForm(forms.Form):
    """Form for resetting password"""
    new_password = forms.CharField(
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'Enter new password',
            'required': True
        })
    )
    confirm_password = forms.CharField(
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'Confirm new password',
            'required': True
        })
    )

    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)

    def clean_new_password(self):
        new_password = self.cleaned_data.get('new_password')
        if new_password:
            try:
                validate_password(new_password, user=self.user)
            except DjangoValidationError as error:
                raise forms.ValidationError(error.messages)
        return new_password

    def clean(self):
        cleaned_data = super().clean()
        new_password = cleaned_data.get('new_password')
        confirm_password = cleaned_data.get('confirm_password')

        if new_password and confirm_password and new_password != confirm_password:
            raise forms.ValidationError("Passwords do not match.")

        return cleaned_data
