from datetime import datetime

from django.http import Http404
from django.shortcuts import render

# Create your views here.
from api.models import Launch
from app.models import Translator, Staff


def translator_view(request, ):
    translators = Translator.objects.all()
    previous_launches = Launch.objects.filter(net__lte=datetime.now()).order_by('-net')[:5]
    return render(request, 'web/about/translators.html', {'translators': translators,
                                                          'previous_launches': previous_launches})


def staff_view(request, ):
    staff = Staff.objects.all()
    previous_launches = Launch.objects.filter(net__lte=datetime.now()).order_by('-net')[:5]
    return render(request, 'web/about/staff.html', {'staff': staff,
                                                    'previous_launches': previous_launches})


def about_view(request, ):
    previous_launches = Launch.objects.filter(net__lte=datetime.now()).order_by('-net')[:5]
    return render(request, 'web/about/about.html', {'previous_launches': previous_launches})
