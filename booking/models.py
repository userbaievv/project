from django.db import models
from django.contrib.auth.models import AbstractUser
from django.utils import timezone
from datetime import timedelta
import random

class Restaurant(models.Model):
    name = models.CharField(max_length=100)
    address = models.TextField()

    def __str__(self):
        return self.name

class Table(models.Model):
    number = models.IntegerField()
    seats = models.IntegerField()
    restaurant = models.ForeignKey(Restaurant, on_delete=models.CASCADE)
    is_booked = models.BooleanField(default=False)

    def __str__(self):
        return f"Table {self.number} ({self.seats} seats)"

class CustomUser(models.Model):
    username = models.CharField(max_length=150, unique=True)
    email = models.EmailField(unique=True)
    password = models.CharField(max_length=128)


class RegisteredUser(AbstractUser):
    username = models.CharField(max_length=150, unique=True)
    email = models.EmailField(unique=False)
    password = models.CharField(max_length=128)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.username

class Reservation(models.Model):
    table = models.ForeignKey(Table, on_delete=models.CASCADE)
    customer_name = models.CharField(max_length=100)
    date = models.DateTimeField()
    user = models.ForeignKey(RegisteredUser, on_delete=models.CASCADE,default=1)

    def __str__(self):
        return f"{self.customer_name} - {self.date}"

from django.conf import settings

class BookingTable(models.Model):
    customer = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    table = models.ForeignKey(Table, on_delete=models.CASCADE)
    guests_count = models.PositiveIntegerField()
    booking_date = models.DateField()
    booking_time = models.TimeField()

    def __str__(self):
        return f"Столик {self.table} - {self.customer.username}"


class PhoneVerification(models.Model):
    phone_number = models.CharField(max_length=15)
    code = models.CharField(max_length=6)
    created_at = models.DateTimeField(auto_now_add=True)

    def is_expired(self):
        return timezone.now() > self.created_at + timedelta(minutes=2)

    @staticmethod
    def generate_code():
        return str(random.randint(100000, 999999))
