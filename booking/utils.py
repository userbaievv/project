from rest_framework.views import exception_handler
from django.shortcuts import render
import requests
import urllib.parse

def custom_exception_handler(exc, context):
    response = exception_handler(exc, context)

    if response is not None and response.status_code == 403:
        request = context['request']
        return render(request, 'booking/no-permission.html', status=403)

    return response




def send_sms(phone, code):
    api_key = ''
    phone = phone.lstrip('+')
    text = f'Ваш код подтверждения: {code}. DjangoProject (проект студента университета IITU)'

    url = 'https://api.mobizon.kz/service/message/sendsmsmessage'
    params = {
        'apiKey': api_key,
        'recipient': phone,
        'text': text,
    }

    try:
        response = requests.get(url, params=params, timeout=10)
        response.raise_for_status()
        data = response.json()
        print("SMS sent:", data)
        return data
    except requests.RequestException as e:
        print("Error sending SMS:", e)
        return None

