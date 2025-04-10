from rest_framework import serializers
from .models import BookingTable

class BookingTableSerializer(serializers.ModelSerializer):
    class Meta:
        model = BookingTable
        fields = '__all__'
