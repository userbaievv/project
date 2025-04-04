from django.contrib.auth.forms import UserCreationForm
from django import forms


class CustomUserCreationForm(UserCreationForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.fields['username'].label = 'Имя пользователя'
        self.fields['username'].help_text = 'Введите имя пользователя'

        self.fields['password1'].label = 'Пароль'
        self.fields['password1'].help_text = ''

        self.fields['password2'].label = 'Подтверждение пароля'
        self.fields['password2'].help_text = ''