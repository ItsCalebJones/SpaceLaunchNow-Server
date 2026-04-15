from django.contrib import admin, messages
from django.utils import timezone

from . import models
from .firebase_rc_service import update_pinned_content


# Register your models here.
@admin.register(models.AppConfig)
class AppConfigAdmin(admin.ModelAdmin):
    icon = '<i class="material-icons">assignment</i>'
    list_display = ("id",)


@admin.register(models.Translator)
class TranslatorAdmin(admin.ModelAdmin):
    icon = '<i class="material-icons">assignment</i>'
    list_display = (
        "id",
        "name",
    )


@admin.register(models.Staff)
class StaffAdmin(admin.ModelAdmin):
    icon = '<i class="material-icons">assignment</i>'
    list_display = (
        "id",
        "name",
    )


@admin.register(models.Nationality)
class NationalityAdmin(admin.ModelAdmin):
    icon = '<i class="material-icons">assignment</i>'
    list_display = (
        "id",
        "name",
    )


@admin.register(models.PinnedContent)
class PinnedContentAdmin(admin.ModelAdmin):
    icon = '<i class="material-icons">push_pin</i>'
    list_display = ("content_type", "content_id", "enabled", "expires_at", "last_synced_at")
    readonly_fields = ("last_synced_at",)
    fieldsets = (
        (None, {"fields": ("content_type", "content_id", "enabled")}),
        ("Details", {"fields": ("expires_at", "custom_message")}),
        ("Sync Status", {"fields": ("last_synced_at",)}),
    )

    def save_model(self, request, obj, form, change):
        super().save_model(request, obj, form, change)
        json_value = obj.to_remote_config_json()
        success = update_pinned_content(json_value)
        if success:
            obj.last_synced_at = timezone.now()
            obj.save()
            messages.success(request, "Pinned content synced to Firebase Remote Config.")
        else:
            messages.warning(
                request,
                "Pinned content saved locally but failed to sync to Firebase Remote Config. "
                "Check server logs for details.",
            )


@admin.register(models.EventNotificationProxy)
class EventNotificationProxyAdmin(admin.ModelAdmin):
    icon = '<i class="material-icons">notifications</i>'
    list_display = ("name", "date", "notifications_enabled")
    list_editable = ("notifications_enabled",)
    list_filter = ("notifications_enabled",)
    search_fields = ("name",)
    fields = ("name", "date", "notifications_enabled")
    readonly_fields = ("name", "date")
