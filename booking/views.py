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
import os
from dotenv import load_dotenv
load_dotenv()
from django.db import connection



import g4f
import json
from django.views.decorators.csrf import csrf_exempt
from django.db.models import Q
import re


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
    booked_tables = today_bookings.values_list('table', flat=True)

    all_tables = []
    for i in range(1, 12):
        all_tables.append({
            'id': i,
            'booked': i in booked_tables,
            'editing': False
        })

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
        'tables': all_tables,
        'editing_table_id': None,
        'chair_angles': [0, 60, 120, 180, 240, 300],
    })



@login_required
def booking_update(request, pk):
    booking = get_object_or_404(BookingTable, pk=pk)
    if booking.customer != request.user and not request.user.is_superuser:
        return redirect('booking_list')

    form = BookingForm(request.POST or None, instance=booking)

    today = now().date()
    today_bookings = BookingTable.objects.filter(booking_date=today)
    chair_angles = [0, 60, 120, 180, 240, 300]
    booked_tables = today_bookings.values_list('table', flat=True)

    all_tables = []
    for i in range(1, 12):
        all_tables.append({
            'id': i,
            'booked': i in booked_tables and i != booking.table.id,
            'editing': booking.table.id == i
        })

    if form.is_valid():
        form.save()
        return redirect('booking_list')

    return render(request, 'booking/booking_form.html', {
        'form': form,
        'tables': all_tables,
        'editing_table_id': booking.table,
        'chair_angles': [0, 60, 120, 180, 240, 300],
    })

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
    mobizon_api = os.getenv('mobizon_api')
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
    mobizon_api = os.getenv('mobizon_api')
    if not phone:
        return JsonResponse({"error": "Телефон не найден в сессии"}, status=400)

    code = PhoneVerification.generate_code()
    PhoneVerification.objects.create(phone_number=phone, code=code)
    send_sms(phone, code)

    return JsonResponse({"message": "Код отправлен заново"})

from django.shortcuts import render

def test_home(request):
    return render(request, 'homehome.html')

def contacts(request):
    google_maps_api = os.getenv('google_maps_api')
    return render(request, 'contacts.html',{'google_maps_api': google_maps_api})



@csrf_exempt
def chat_support(request):
    if request.method == 'POST':
        data = json.loads(request.body)
        question = data.get('question', '')
        history = data.get('history', [])

        booking_date = None
        booking_time = None
        table_number = None

        date_match = re.search(r"(\d{1,2})\s*(января|февраля|марта|апреля|мая|июня|июля|августа|сентября|октября|ноября|декабря|\d{4})", question)
        if date_match:
            day = date_match.group(1)
            month_str = date_match.group(2)
            months = {
                "января": "01", "февраля": "02", "марта": "03", "апреля": "04", "мая": "05",
                "июня": "06", "июля": "07", "августа": "08", "сентября": "09", "октября": "10",
                "ноября": "11", "декабря": "12"
            }
            month = months.get(month_str, None)
            if month:
                booking_date = f"2025-{month}-{day.zfill(2)}"

        if "все брони" in question:
            if booking_date:
                bookings = BookingTable.objects.filter(booking_date=booking_date)
                if bookings.exists():
                    response = f"На {booking_date} забронированы следующие столы: "
                    response += ", ".join([f"Стол {booking.table}, {booking.booking_time}" for booking in bookings])
                else:
                    response = f"На {booking_date} нет забронированных столов."

        elif "свободен ли стол" in question and booking_date:
            table_match = re.search(r"стол (\d+)", question)
            if table_match:
                table_number = int(table_match.group(1))

            time_match = re.search(r"(\d{1,2}:\d{2})", question)
            if time_match:
                booking_time = time_match.group(1)

            if table_number and booking_date and booking_time:
                booked_table = BookingTable.objects.filter(
                    Q(booking_date=booking_date) &
                    Q(booking_time=booking_time) &
                    Q(table=table_number)
                )

                if booked_table.exists():
                    response = f"Стол {table_number} занят на {booking_date} в {booking_time}."
                else:
                    response = f"Стол {table_number} свободен на {booking_date} в {booking_time}."
            elif table_number and booking_date:
                available_tables = BookingTable.objects.filter(
                    Q(booking_date=booking_date) &
                    Q(table=table_number)
                )

                if available_tables.exists():
                    response = f"Стол {table_number} занят на {booking_date}."
                else:
                    response = f"Стол {table_number} свободен на {booking_date}."

        else:
            try:
                response = g4f.ChatCompletion.create(
                    model="gpt-4o",
                    messages=[
                        {"role": "system", "content": "Ты помощник сайта ресторана 'Гурман'. Отвечай на вопросы о бронировании, часах работы, адресе, контактной информации и меню. Если спрашивают контакты Тел: 8 (777) 777 7777 Эл. адрес: 40387@iitu.edu.kz, 40256@iitu.edu.kz. Режим работы: Пн-Пт: с 11:00 до 23:00 Сб-Вс: с 12:00 до 22:00  Адрес: г. Алматы, Улица Курмангазы 79"},
                        *history,
                        {"role": "user", "content": question}
                    ]
                )
            except Exception as e:
                response = "Извините, возникла ошибка. Попробуйте позже."

        return JsonResponse({'response': response})