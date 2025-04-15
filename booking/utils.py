from rest_framework.views import exception_handler
from django.shortcuts import render

def custom_exception_handler(exc, context):
    response = exception_handler(exc, context)

    if response is not None and response.status_code == 403:
        request = context['request']
        return render(request, 'booking/no-permission.html', status=403)

    return response