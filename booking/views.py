from django.shortcuts import render, redirect,get_object_or_404
from django.contrib.auth import login, logout, authenticate, get_user_model
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth.models import User
from django.contrib.auth.decorators import login_required
from .models import BookingTable, RegisteredUser, PhoneVerification, Table
from .forms import RegistrationForm ,CustomUserCreationForm, BookingForm, BookingFilterForm
from django.http import JsonResponse
from .utils import send_sms
from django.utils.timezone import now
import os
from dotenv import load_dotenv
load_dotenv()
from django.db import connection
from .serializers import BookingTableSerializer
from datetime import datetime, timedelta, timezone
import g4f
import json
from django.views.decorators.csrf import csrf_exempt
from django.db.models import Q
import re
import pytz

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
            return redirect('home')

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
    almaty_tz = pytz.timezone('Asia/Almaty')
    almaty_now = datetime.now(almaty_tz)
    today = almaty_now.date()

    today_bookings = BookingTable.objects.filter(booking_date=today)
    booked_tables = today_bookings.values_list('table', flat=True)

    booked_table_numbers = set(
        BookingTable.objects.filter(booking_date=today)
        .select_related("table")
        .values_list("table__number", flat=True)
    )

    form = BookingForm(request.POST or None, booked_table_numbers=booked_table_numbers)

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

        selected_datetime = datetime.combine(booking_date, booking_time)
        selected_datetime = almaty_tz.localize(selected_datetime)

        if selected_datetime < almaty_now:
            form.add_error('booking_time', 'Нельзя выбрать прошедшее время.')
        else:
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


def test_home(request):
    return render(request, 'homehome.html')

def contacts(request):
    google_maps_api = os.getenv('google_maps_api')
    return render(request, 'contacts.html',{'google_maps_api': google_maps_api})

@csrf_exempt
@login_required
def chat_support(request):
    if request.method == 'POST':
        data = json.loads(request.body)
        question = data.get('question', '')
        history = data.get('history', [])
        user = request.user

        bookings = BookingTable.objects.filter(customer=user).order_by('booking_date', 'booking_time')
        booking_info = [
            f"ID: {b.id} | Стол {b.table} — {b.booking_date} в {b.booking_time}"
            for b in bookings
        ]
        booking_data = "\n".join(booking_info) or "У вас нет активных бронирований."

        try:
            response = g4f.ChatCompletion.create(
                model="gpt-4o",
                messages=[
                    {
                        "role": "system",
                        "content": (
                            "Ты помощник ресторана 'Гурман'. Отвечай на вопросы о меню, часах работы, адресе и бронированиях.\n\n"
                            "Если спрашивают контакты Тел: 8 (777) 777 7777 Эл. адрес: 40387@iitu.edu.kz, 40256@iitu.edu.kz.\n"
                            "Если спрашивают Режим работы: Пн-Пт: с 11:00 до 23:00 Сб-Вс: с 12:00 до 22:00.\n"
                            "Если спрашивают Адрес: г. Алматы, Улица Курмангазы 79. \n"
                            "УДАЛЕНИЕ БРОНИ:\n"
                            "Если пользователь хочет удалить бронь:\n"
                            "1. Спроси, какую бронь (дату, время, стол).\n"
                            "2. Покажи варианты, если есть несколько.\n"
                            "3. Обязательно спроси подтверждение: 'Вы точно хотите удалить бронь стола {номер} на {дата} в {время}?' \n"
                            "4. После подтверждения — ответь строго в формате: DEL:{ID}\n\n"
                            "СОЗДАНИЕ БРОНИ:\n"
                            "Если пользователь хочет создать бронь:\n"
                            "1. Спроси, на какую дату, время и сколько гостей.\n"
                            "2. Покажи доступные столы.\n"
                            "3. После выбора и подтверждения пользователя — ответь строго в формате: CREATE:{table_id}:{guests}:{date}:{time}.\n"
                            "Пример: CREATE:5:3:2025-04-25:19:00\n\n"
                            f"Актуальные брони пользователя:\n{booking_data}"
                        )
                    },
                    *history,
                    {"role": "user", "content": question}
                ]
            )

            bot_reply = response.strip()

            if bot_reply.startswith("DEL:"):
                try:
                    booking_id = int(bot_reply.replace("DEL:", "").strip())
                    booking = BookingTable.objects.get(id=booking_id, customer=user)
                    booking.delete()
                    return JsonResponse({'response': f'✅ Бронь удалена: Стол {booking.table} на {booking.booking_date} в {booking.booking_time}.'})
                except BookingTable.DoesNotExist:
                    return JsonResponse({'response': f'❌ Бронь с ID {booking_id} не найдена или не принадлежит вам.'})

            elif bot_reply.startswith("CREATE:"):
                try:
                    parts = bot_reply.replace("CREATE:", "").split(":")
                    table_id, guests, date, time = int(parts[0]), int(parts[1]), parts[2], parts[3]
                    table = Table.objects.get(id=table_id)

                    exists = BookingTable.objects.filter(
                        table=table,
                        booking_date=date,
                        booking_time=time
                    ).exists()

                    if exists:
                        return JsonResponse({'response': '❌ Этот столик уже занят на указанное время. Попробуйте другой.'})

                    booking = BookingTable.objects.create(
                        customer=user,
                        table=table,
                        guests_count=guests,
                        booking_date=date,
                        booking_time=time
                    )
                    return JsonResponse({'response': f'✅ Бронь создана: Стол {table} на {date} в {time} для {guests} гостей. (ID: {booking.id})'})
                except Exception as e:
                    return JsonResponse({'response': '❌ Ошибка при создании брони. Проверьте данные.'})

            return JsonResponse({'response': bot_reply})

        except Exception as e:
            return JsonResponse({'response': '❌ Ошибка сервера. Попробуйте позже.'})
