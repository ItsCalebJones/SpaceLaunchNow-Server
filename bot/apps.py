# -*- coding: utf-8 -*-
from __future__ import unicode_literals
from django.apps import AppConfig


class BotConfig(AppConfig):
    name = 'bot'

    def ready(self):
        from bot.app import bot_main
        bot_main.start_scheduler()
