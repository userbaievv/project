from django.contrib.auth.forms import UserCreationForm
from django import forms
from .models import RegisteredUser, BookingTable

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


class BookingForm(forms.ModelForm):
    class Meta:
        model = BookingTable
        fields = ['table_number', 'guests_count', 'booking_date', 'booking_time']
        widgets = {
            'booking_date': forms.DateInput(attrs={'type': 'date'}),
            'booking_time': forms.TimeInput(attrs={'type': 'time'}),
        }