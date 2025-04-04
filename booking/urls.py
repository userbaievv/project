from django.contrib import admin
from django.urls import path
from . import views

urlpatterns = [
    path('', views.home, name='home'),
    path('booking/', views.booking, name='booking'),
    path('book/<int:table_id>/', views.book_table, name='book_table'),
    path('register/', views.register, name='register'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('register/', views.register_view, name='register'),

]
from django.contrib.auth import views as auth_views
from .views import (
    reservation_create, reservation_list,
    reservation_update, reservation_delete,
)

urlpatterns = [
    path('', reservation_list, name='home'),
    path('reservations/', reservation_list, name='reservation_list'),
    path('reservations/new/', reservation_create, name='reservation_create'),
    path('reservations/<int:pk>/edit/', reservation_update, name='reservation_update'),
    path('reservations/<int:pk>/delete/', reservation_delete, name='reservation_delete'),
    path('logout/', auth_views.LogoutView.as_view(), name='logout'),
]
