"""
WSGI config for spacelaunchnow project.

It exposes the WSGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/1.11/howto/deployment/wsgi/
"""

import os

from django.core.wsgi import get_wsgi_application

from spacelaunchnow.telemetry import init_telemetry

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "spacelaunchnow.settings")
os.environ["HTTPS"] = "on"

init_telemetry()

application = get_wsgi_application()
