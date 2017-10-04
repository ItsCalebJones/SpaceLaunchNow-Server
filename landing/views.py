# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.shortcuts import render


# Create your views here.
def index(request):
    return render(request, 'landing/index.html',)


# Create your views here.
def next_launch(request):
    return render(request, 'next/next.html',)
