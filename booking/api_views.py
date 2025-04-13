from rest_framework import viewsets
from .models import BookingTable
from .serializers import BookingTableSerializer
from rest_framework.permissions import IsAuthenticated

class BookingTableViewSet(viewsets.ModelViewSet):
    queryset = BookingTable.objects.all()
    serializer_class = BookingTableSerializer
    permission_classes = [IsAuthenticated]


    def get_queryset(self):
        user = self.request.user
        if user.is_superuser:
            return BookingTable.objects.all()
        return BookingTable.objects.filter(customer=user)

    def perform_create(self, serializer):
        serializer.save(customer=self.request.user)


