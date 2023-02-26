from django.urls import reverse_lazy
from django.views.generic import CreateView

from .forms import ChangeForm, CreationForm, NewPass


class SignUp(CreateView):
    form_class = CreationForm
    success_url = reverse_lazy('posts:index')
    template_name = 'users/signup.html'


class PasswordChange(CreateView):
    form_class = ChangeForm
    success_url = reverse_lazy('users:successful_change')
    template_name = 'users/password_change_form.html'


class PasswordReset(CreateView):
    form_class = NewPass
    success_url = reverse_lazy('users:successful_reset')
    template_name = 'users/password_reset_form.html'
