from rest_framework import serializers
from .models import BookingTable

class BookingTableSerializer(serializers.ModelSerializer):
    customer = serializers.CharField(source='customer.username')

    class Meta:
        model = BookingTable
        fields = '__all__'
