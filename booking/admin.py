from django.contrib import admin
from .models import Restaurant, Table, Reservation, RegisteredUser, BookingTable

admin.site.register(RegisteredUser)

admin.site.register(Restaurant)
admin.site.register(Table)
admin.site.register(Reservation)

@admin.register(BookingTable)
class BookingTableAdmin(admin.ModelAdmin):
    list_display = ('table_number', 'guests_count', 'booking_date', 'booking_time', 'customer')
    list_filter = ('booking_date',)
    search_fields = ('table_number', 'customer__username')