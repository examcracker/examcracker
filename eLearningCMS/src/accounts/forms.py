from __future__ import unicode_literals
from django.contrib.auth.forms import AuthenticationForm
from django import forms
from crispy_forms.helper import FormHelper
from crispy_forms.layout import Layout, Submit, HTML, Field
from authtools import forms as authtoolsforms
from django.contrib.auth import forms as authforms
from django.urls import reverse
import student
import provider

class LoginForm(AuthenticationForm):
    remember_me = forms.BooleanField(required=False, initial=False)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.fields["username"].widget.input_type = "email"  # ugly hack

        self.helper.layout = Layout(
            Field('username', placeholder="Enter Email", autofocus=""),
            Field('password', placeholder="Enter Password"),
            HTML('<a href="{}">Forgot Password?</a>'.format(
                reverse("accounts:password-reset"))),
            Field('remember_me'),
            Submit('sign_in', 'Log in',
                   css_class="btn btn-lg btn-primary btn-block"),
        )

class RegisterForm(authtoolsforms.UserCreationForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.fields["email"].widget.input_type = "email"

        self.helper.layout = Layout(
            Field('email', placeholder="Enter Email", autofocus=""),
            Field('name', placeholder="Enter Full Name"),
            Field('password1', placeholder="Enter Password"),
            Field('password2', placeholder="Re Enter Password"),
            Submit('sign_up', 'Sign up', css_class="btn-warning"),
        )

class SignupForm(RegisterForm):
    def save(self, commit=True):
        signedupuser = super(SignupForm, self).save(commit=False)
        signedupuser.is_staff = False
        signedupuser.save()

        studentobj = student.models.Student(user=signedupuser)
        studentobj.save()
        return signedupuser

class RegisterProviderForm(RegisterForm):
    def save(self, commit=True):
        signedupuser = super(RegisterProviderForm, self).save(commit=False)
        signedupuser.is_staff = True
        signedupuser.save()

        providerobj = provider.models.Provider(user=signedupuser)
        providerobj.save()
        return signedupuser


class PasswordChangeForm(authforms.PasswordChangeForm):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()

        self.helper.layout = Layout(
            Field('old_password', placeholder="Enter old password",
                  autofocus=""),
            Field('new_password1', placeholder="Enter new password"),
            Field('new_password2', placeholder="Enter new password (again)"),
            Submit('pass_change', 'Change Password', css_class="btn-warning"),
        )


class PasswordResetForm(authtoolsforms.FriendlyPasswordResetForm):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()

        self.helper.layout = Layout(
            Field('email', placeholder="Enter email",
                  autofocus=""),
            Submit('pass_reset', 'Reset Password', css_class="btn-warning"),
        )


class SetPasswordForm(authforms.SetPasswordForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()

        self.helper.layout = Layout(
            Field('new_password1', placeholder="Enter new password",
                  autofocus=""),
            Field('new_password2', placeholder="Enter new password (again)"),
            Submit('pass_change', 'Change Password', css_class="btn-warning"),
        )
