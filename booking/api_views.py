from rest_framework import viewsets
from .models import BookingTable
from .serializers import BookingTableSerializer
from rest_framework.permissions import IsAdminUser

class BookingTableViewSet(viewsets.ModelViewSet):
    queryset = BookingTable.objects.all()
    serializer_class = BookingTableSerializer
    permission_classes = [IsAdminUser]