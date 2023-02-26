from django.contrib.auth import get_user_model
from django.contrib.auth.forms import (PasswordChangeForm, PasswordResetForm,
                                       UserCreationForm)

User = get_user_model()


class CreationForm(UserCreationForm):
    class Meta(UserCreationForm.Meta):
        model = User

        fields = ('first_name', 'last_name', 'username', 'email')


class ChangeForm(PasswordChangeForm):
    fields = ('old_password', 'new_password', 'new_password_repeat')


class NewPass(PasswordResetForm):
    fields = ('new_password', 'new_password_repeat')
