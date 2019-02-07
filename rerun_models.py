import asyncio
import datetime
import logging
import os
import sys
import traceback
from collections import Counter

import discord
import django
from discord.ext import commands
from django.template import defaultfilters

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "spacelaunchnow.settings")
django.setup()

from api.models import *


if __name__ == '__main__':
    agencies = Agency.objects.all()

    spacecraft_configs = SpacecraftConfiguration.objects.all()

    launcher_configs = LauncherConfig.objects.all()

    launchers = Launcher.objects.all()

    length = len(agencies)
    print("Agencies Count: %s", length)
    for count, item in enumerate(agencies):
        print("Agency - %s of %s - %s" % (count, length, item.name))
        item.save()

    length = len(spacecraft_configs)
    print("SpacecraftConfigs Count: %s", length)
    for count, item in enumerate(spacecraft_configs):
        print("SpacecraftConfigs - %s of %s - %s" % (count, length, item.name))
        item.save()

    length = len(launcher_configs)
    print("LauncherConfigs Count: %s", length)
    for count, item in enumerate(launcher_configs):
        print("LauncherConfigs - %s of %s - %s" % (count, length, item.name))
        item.save()

    length = len(launchers)
    print("Launchers Count: %s", length)
    for count, item in enumerate(launchers):
        print("Launchers - %s of %s - %s" % (count, length, item.id))
        item.save()
