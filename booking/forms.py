from django.contrib.auth.forms import UserCreationForm
from django import forms
from .models import RegisteredUser
from .models import Reservation
class CustomUserCreationForm(UserCreationForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.fields['username'].label = 'Имя пользователя'
        self.fields['username'].help_text = 'Введите имя пользователя'

        self.fields['password1'].label = 'Пароль'
        self.fields['password1'].help_text = ''

        self.fields['password2'].label = 'Подтверждение пароля'
        self.fields['password2'].help_text = ''


class RegistrationForm(forms.ModelForm):
    class Meta:
        model = RegisteredUser
        fields = ['username', 'email', 'password']
        widgets = {
            'password': forms.PasswordInput()
        }



class ReservationForm(forms.ModelForm):
    class Meta:
        model = Reservation
        fields = ['customer_name', 'date', 'table']
        widgets = {
            'date': forms.DateTimeInput(attrs={'type': 'datetime-local'}),
        }