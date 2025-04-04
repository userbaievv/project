from django.contrib import admin
from .models import Restaurant, Table, Reservation
from .models import RegisteredUser

admin.site.register(RegisteredUser)

admin.site.register(Restaurant)
admin.site.register(Table)
admin.site.register(Reservation)

