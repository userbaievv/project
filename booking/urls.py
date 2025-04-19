from django.urls import path
from . import views
from .views import register_phone_view, verify_sms_view, resend_code_view

urlpatterns = [
    path('', views.test_home, name='home'),
    path('register/', views.register_view, name='register'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('bookings/', views.booking_list, name='booking_list'),
    path('bookings/new/', views.booking_create, name='booking_create'),
    path('bookings/<int:pk>/edit/', views.booking_update, name='booking_update'),
    path('bookings/<int:pk>/delete/', views.booking_delete, name='booking_delete'),
    path('no-permission/', views.no_permission_view, name='no_permission'),
    path('register-phone/', register_phone_view, name='register_phone'),
    path('verify-sms/', verify_sms_view, name='verify_sms'),
    path("resend-code/", resend_code_view, name="resend_code"),
    path('reg/',views.home, name='reg'),
    path('contacts/',views.contacts,name='contacts'),
    path('chat-support/', views.chat_support, name='chat_support'),
]