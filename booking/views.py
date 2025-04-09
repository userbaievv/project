from django.shortcuts import render, redirect,get_object_or_404
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth.decorators import login_required
from .models import BookingTable, RegisteredUser
from .forms import RegistrationForm ,CustomUserCreationForm, BookingForm, BookingFilterForm
from django.shortcuts import render, redirect
from .forms import RegistrationForm

def home(request):
    return render(request, 'booking/home.html')

def login_view(request):
    form = AuthenticationForm()
    if request.method == "POST":
        form = AuthenticationForm(data=request.POST)
        if form.is_valid():
            user = form.get_user()
            login(request, user)
            return redirect('booking_list')
    return render(request, 'booking/login.html', {'form': form})

def logout_view(request):
    logout(request)
    return redirect('home')

from django.contrib.auth import login

def register_view(request):
    if request.user.is_authenticated:
        return redirect('home')

    if request.method == "POST":
        username = request.POST['username']
        password1 = request.POST['password1']
        password2 = request.POST['password2']

        if password1 != password2 or len(password1) < 5:
            return redirect('home')  # или показать ошибку

        user = RegisteredUser.objects.create_user(username=username, password=password1)
        login(request, user)
        return redirect('booking_list')

    return redirect('home')


@login_required
def booking_list(request):
    bookings = BookingTable.objects.filter(customer=request.user)
    form = BookingFilterForm(request.GET)

    if form.is_valid():
        date = form.cleaned_data.get('date')
        guests_count = form.cleaned_data.get('guests_count')
        sort_by = form.cleaned_data.get('sort_by')

        if date:
            bookings = bookings.filter(booking_date=date)
        if guests_count:
            bookings = bookings.filter(guests_count=guests_count)
        if sort_by:
            bookings = bookings.order_by(sort_by)

    return render(request, 'booking/booking_list.html', {
        'bookings': bookings,
        'filter_form': form,
    })

@login_required
def booking_create(request):
    form = BookingForm(request.POST or None)
    if form.is_valid():
        booking = form.save(commit=False)
        booking.customer = request.user
        booking.save()
        return redirect('booking_list')
    return render(request, 'booking/booking_form.html', {'form': form})

@login_required
def booking_update(request, pk):
    booking = get_object_or_404(BookingTable, pk=pk)
    if booking.customer != request.user:
        return redirect('booking_list')
    form = BookingForm(request.POST or None, instance=booking)
    if form.is_valid():
        form.save()
        return redirect('booking_list')
    return render(request, 'booking/booking_form.html', {'form': form})

@login_required
def booking_delete(request, pk):
    booking = get_object_or_404(BookingTable, pk=pk)
    if request.method == 'POST':
        booking.delete()
        return redirect('booking_list')
    return render(request, 'booking/booking_confirm_delete.html', {'booking': booking})
