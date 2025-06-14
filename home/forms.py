from django import forms
from django.contrib.auth.forms import UserCreationForm
from .models import User

# Django forms simplify handling and validating form data.

class SignUpForm(UserCreationForm):
    """
    A form for creating new users. It extends the default UserCreationForm
    to include first name, last name, and email fields.
    """
    first_name = forms.CharField(max_length=30, required=True, help_text='Required.')
    last_name = forms.CharField(max_length=30, required=True, help_text='Required.')
    email = forms.EmailField(max_length=254, required=True, help_text='Required. Inform a valid email address.')

    class Meta(UserCreationForm.Meta):
        model = User
        fields = UserCreationForm.Meta.fields + ('first_name', 'last_name', 'email')

class LoginForm(forms.Form):
    """
    A simple form for user login, containing username and password fields.
    """
    username = forms.CharField()
    password = forms.CharField(widget=forms.PasswordInput)
