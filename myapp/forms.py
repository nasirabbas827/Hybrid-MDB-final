from django import forms
from django.contrib.auth.hashers import make_password
from .models import UserRegister


class UserRegisterForm(forms.ModelForm):
    password = forms.CharField(
        widget=forms.PasswordInput(attrs={'class': 'form-control', 'placeholder': 'Enter password'})
    )

    class Meta:
        model = UserRegister
        fields = ['full_name', 'email', 'password', 'role', 'gender', 'phone']
        widgets = {
            'full_name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Enter full name'}),
            'email': forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'Enter email'}),
            'role': forms.Select(attrs={'class': 'form-control'}),
            'gender': forms.Select(attrs={'class': 'form-control'}),
            'phone': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Enter phone number'}),
        }

    def save(self, commit=True):
        user = super().save(commit=False)
        user.password = make_password(self.cleaned_data['password'])  # hash password
        if commit:
            user.save()
        return user


class LoginForm(forms.Form):
    email = forms.EmailField(widget=forms.EmailInput(attrs={
        'class': 'form-control', 'placeholder': 'Enter email'
    }))
    password = forms.CharField(widget=forms.PasswordInput(attrs={
        'class': 'form-control', 'placeholder': 'Enter password'
    }))
    role = forms.ChoiceField(choices=[('teacher', 'Teacher'), ('student', 'Student')],
                             widget=forms.Select(attrs={'class': 'form-control'}))


class UpdateProfileForm(forms.ModelForm):
    class Meta:
        model = UserRegister
        fields = [
            'full_name', 'email', 'gender', 'dob', 'profile_picture',
            'phone', 'bio', 'country', 'city'
        ]
        widgets = {
            'full_name': forms.TextInput(attrs={'class': 'form-control'}),
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
            'gender': forms.Select(attrs={'class': 'form-control'}),
            'dob': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'phone': forms.TextInput(attrs={'class': 'form-control'}),
            'bio': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'country': forms.TextInput(attrs={'class': 'form-control'}),
            'city': forms.TextInput(attrs={'class': 'form-control'}),
        }


from django import forms
from .models import MDBMessage

class MDBPostForm(forms.ModelForm):
    class Meta:
        model = MDBMessage
        fields = ['content']
        widgets = {
            'content': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Type your message here...'
            }),
        }
        labels = {
            'content': 'Message',
        }


from django import forms
from .models import GlobalKeyword

class GlobalKeywordForm(forms.ModelForm):
    academic_keywords = forms.CharField(
        widget=forms.Textarea(attrs={'rows': 5, 'placeholder': 'Comma-separated academic keywords'}),
        required=False
    )
    non_academic_keywords = forms.CharField(
        widget=forms.Textarea(attrs={'rows': 5, 'placeholder': 'Comma-separated non-academic keywords'}),
        required=False
    )

    class Meta:
        model = GlobalKeyword
        fields = ['academic_keywords', 'non_academic_keywords']