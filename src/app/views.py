from datetime import datetime

# Create your views here.
from api.models import Launch
from django.shortcuts import render

from app.models import Staff, Translator


def translator_view(
    request,
):
    translators = Translator.objects.all()
    previous_launches = Launch.objects.filter(net__lte=datetime.now()).order_by("-net")[
        :10
    ]
    return render(
        request,
        "web/about/translators.html",
        {"translators": translators, "previous_launches": previous_launches},
    )


def staff_view(
    request,
):
    staff = Staff.objects.all()
    previous_launches = Launch.objects.filter(net__lte=datetime.now()).order_by("-net")[
        :10
    ]
    return render(
        request,
        "web/about/staff.html",
        {"staff": staff, "previous_launches": previous_launches},
    )


def about_view(
    request,
):
    previous_launches = Launch.objects.filter(net__lte=datetime.now()).order_by("-net")[
        :10
    ]
    return render(
        request, "web/about/about.html", {"previous_launches": previous_launches}
    )
