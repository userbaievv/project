from rest_framework.routers import DefaultRouter
from .api_views import BookingTableViewSet

router = DefaultRouter()
router.register(r'bookings', BookingTableViewSet)

urlpatterns = router.urls
