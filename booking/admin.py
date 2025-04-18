from django.contrib import admin
from .models import Restaurant, Table, Reservation, RegisteredUser, BookingTable
from django.contrib.auth.admin import UserAdmin
from django.utils.translation import gettext_lazy as _

admin.site.register(Restaurant)
admin.site.register(Table)
admin.site.register(Reservation)

@admin.register(BookingTable)
class BookingTableAdmin(admin.ModelAdmin):
    list_display = ('table', 'guests_count', 'booking_date', 'booking_time', 'customer')
    list_filter = ('booking_date',)
    search_fields = ('table', 'customer__username')


@admin.register(RegisteredUser)
class CustomUserAdmin(UserAdmin):
    fieldsets = (
        (None, {"fields": ("username", "phone_number", "password")}),
        (_("Permissions"), {"fields": ("is_superuser", "is_active")}),
        (_("Important dates"), {"fields": ("last_login","date_joined")}),
    )

    add_fieldsets = (
        (None, {
            "classes": ("wide",),
            "fields": ("username", "phone_number", "password1", "password2"),
        }),
    )

    list_display = ("username", "phone_number", "is_active", "is_superuser",)
    search_fields = ("username", "phone_number")
    ordering = ("id",)