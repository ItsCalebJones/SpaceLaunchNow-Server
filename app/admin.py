from django.contrib import admin
from . import models


# Register your models here.
@admin.register(models.AppConfig)
class AppConfigAdmin(admin.ModelAdmin):
    icon = '<i class="material-icons">assignment</i>'
    list_display = ('id',)


@admin.register(models.Translator)
class TranslatorAdmin(admin.ModelAdmin):
    icon = '<i class="material-icons">assignment</i>'
    list_display = ('id', 'name',)


@admin.register(models.Language)
class LanguageAdmin(admin.ModelAdmin):
    icon = '<i class="material-icons">assignment</i>'
    list_display = ('id', 'name',)