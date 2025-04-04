
from django.shortcuts import render, redirect
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.forms import AuthenticationForm
from .models import Table
from .forms import CustomUserCreationForm
from django.shortcuts import render, redirect
from .forms import RegistrationForm
def home(request):
    form = CustomUserCreationForm()
    if request.method == "POST":
        form = CustomUserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            return redirect('booking')
    return render(request, 'home.html', {'form': form})

def booking(request):
    tables = Table.objects.all()
    return render(request, 'booking.html', {'tables': tables})

def book_table(request, table_id):
    table = Table.objects.get(id=table_id)
    if not table.is_booked:
        table.is_booked = True
        table.save()
    return redirect('booking')

def login_view(request):
    form = AuthenticationForm()
    if request.method == "POST":
        form = AuthenticationForm(data=request.POST)
        if form.is_valid():
            user = form.get_user()
            login(request, user)
            return redirect('booking')
    return render(request, 'login.html', {'form': form})

def logout_view(request):
    logout(request)
    return redirect('home')

def register(request):
    form = CustomUserCreationForm()
    if request.method == "POST":
        form = CustomUserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            return redirect('booking')
    return render(request, 'register.html', {'form': form})



def register_view(request):
    if request.method == 'POST':
        form = RegistrationForm(request.POST)
        if form.is_valid():
            form.save()  # сохраняет в таблицу booking_registereduser
            return redirect('home')  # или куда хочешь
    else:
        form = RegistrationForm()
    return render(request, 'register.html', {'form': form})



from django.shortcuts import render, redirect, get_object_or_404
from .models import Reservation
from .forms import ReservationForm

# Create
def reservation_create(request):
    if request.method == 'POST':
        form = ReservationForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('reservation_list')
    else:
        form = ReservationForm()
    return render(request, 'reservation_form.html', {'form': form})

# Read (список)
def reservation_list(request):
    reservations = Reservation.objects.all()
    return render(request, 'reservation_list.html', {'reservations': reservations})

# Update
def reservation_update(request, pk):
    reservation = get_object_or_404(Reservation, pk=pk)
    form = ReservationForm(request.POST or None, instance=reservation)
    if form.is_valid():
        form.save()
        return redirect('reservation_list')
    return render(request, 'reservation_form.html', {'form': form})

# Delete
def reservation_delete(request, pk):
    reservation = get_object_or_404(Reservation, pk=pk)
    if request.method == 'POST':
        reservation.delete()
        return redirect('reservation_list')
    return render(request, 'reservation_confirm_delete.html', {'reservation': reservation})
