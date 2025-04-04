from django.db import models

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

class Reservation(models.Model):
    table = models.ForeignKey(Table, on_delete=models.CASCADE)
    customer_name = models.CharField(max_length=100)
    date = models.DateTimeField()

    def __str__(self):
        return f"{self.customer_name} - {self.date}"

class CustomUser(models.Model):
    username = models.CharField(max_length=150, unique=True)
    email = models.EmailField(unique=True)
    password = models.CharField(max_length=128)


class RegisteredUser(models.Model):
    username = models.CharField(max_length=150, unique=True)
    email = models.EmailField(unique=True)
    password = models.CharField(max_length=128)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.username