from django.shortcuts import render, redirect,get_object_or_404
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth.decorators import login_required
from .models import BookingTable, RegisteredUser, PhoneVerification
from .forms import RegistrationForm ,CustomUserCreationForm, BookingForm, BookingFilterForm
from django.http import JsonResponse
from .utils import send_sms
from django.utils.timezone import now
from django.contrib.auth import get_user_model


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
    if request.user.is_superuser:
        bookings = BookingTable.objects.all()
    else:
        bookings = BookingTable.objects.filter(customer=request.user)

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

    today = now().date()
    today_bookings = BookingTable.objects.filter(booking_date=today)

    tables_status = {}
    for i in range(1, 11):
        tables_status[f'table{i}'] = {
            'booked': today_bookings.filter(table=i).exists()
        }

    if form.is_valid():
        booking_date = form.cleaned_data['booking_date']
        booking_time = form.cleaned_data['booking_time']
        table = form.cleaned_data['table']

        exists = BookingTable.objects.filter(
            table=table,
            booking_date=booking_date,
            booking_time=booking_time
        ).exists()

        if exists:
            form.add_error('table', 'Этот стол уже забронирован на выбранное время')
        else:
            booking = form.save(commit=False)
            booking.customer = request.user
            booking.save()
            return redirect('booking_list')

    return render(request, 'booking/booking_form.html', {
        'form': form,
        **tables_status,
    })


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


def no_permission_view(request):
    return render(request, 'booking/no-permission.html')

from .models import PhoneVerification
from .utils import send_sms
from django.contrib.auth.models import User

def register_phone_view(request):
    if request.method == "POST":
        phone = request.POST.get("phone")
        username = request.POST.get("username")
        password = request.POST.get("password")
        confirm_password = request.POST.get("confirm_password")
        if password != confirm_password:
            return render(request, "booking/register_phone.html", {"error": "Пароли не совпадают"})

        request.session["reg_phone"] = phone
        request.session["reg_username"] = username
        request.session["reg_password"] = password

        code = PhoneVerification.generate_code()
        PhoneVerification.objects.create(phone_number=phone, code=code)
        send_sms(phone, code)
        return redirect("verify_sms")

    return render(request, "booking/register_phone.html")


def verify_sms_view(request):
    phone = request.session.get("reg_phone")
    if not phone:
        return redirect("register_phone")

    if request.method == "POST":
        code_input = request.POST.get("code")
        try:
            verification = PhoneVerification.objects.filter(phone_number=phone, code=code_input).latest("created_at")
            if verification.is_expired():
                return render(request, "booking/verify_sms.html", {"phone": phone, "error": "Код истёк"})

            username = request.session.get("reg_username")
            password = request.session.get("reg_password")

            User = get_user_model()
            user = User.objects.create_user(username=username, password=password)

            user.phone_number = phone
            user.save()

            login(request, user)
            return redirect("home")
        except PhoneVerification.DoesNotExist:
            return render(request, "booking/verify_sms.html", {"phone": phone, "error": "Неверный код"})

    return render(request, "booking/verify_sms.html", {"phone": phone})

def resend_code_view(request):
    phone = request.session.get("reg_phone")
    if not phone:
        return JsonResponse({"error": "Телефон не найден в сессии"}, status=400)

    code = PhoneVerification.generate_code()
    PhoneVerification.objects.create(phone_number=phone, code=code)
    send_sms(phone, code)

    return JsonResponse({"message": "Код отправлен заново"})