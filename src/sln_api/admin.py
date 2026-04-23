from datetime import timedelta

from django.contrib import admin
from django.contrib.admin import SimpleListFilter
from django.utils import timezone
from django.utils.html import format_html

from .models import (
    Agency,
    Astronaut,
    ConfigLaunchStatus,
    ConfigOrbit,
    Event,
    Expedition,
    Launch,
    Launcher,
    Location,
    Program,
    Spacecraft,
    SpacecraftConfiguration,
    SpaceStation,
    SyncJobConfig,
    Update,
    Vehicle,
)

# ─── Sync Control ─────────────────────────────────────────────────────────────


@admin.register(SyncJobConfig)
class SyncJobConfigAdmin(admin.ModelAdmin):
    list_display = ("sync_type", "enabled", "note", "updated_at")
    list_editable = ("enabled",)
    list_display_links = ("sync_type",)
    readonly_fields = ("sync_type", "updated_at")
    ordering = ("sync_type",)

    def has_add_permission(self, request):
        return False

    def has_delete_permission(self, request, obj=None):
        return False


# ─── Launches ─────────────────────────────────────────────────────────────────


class _DateRangeFilter(SimpleListFilter):
    """Recent / Upcoming / Previous / All filter, defaulting to 'upcoming'.

    Subclasses must set ``date_field`` to the model datetime field to filter on.
    Mirrors the behavior of LL API's ``LaunchDateListFilter`` but with
    'upcoming' as the default selection.
    """

    title = "date"
    parameter_name = "date"
    default_value = "upcoming"
    date_field = ""

    def lookups(self, request, model_admin):
        return (
            ("recent", "Recent"),
            ("upcoming", "Upcoming"),
            ("previous", "Previous"),
            ("all", "All"),
        )

    def choices(self, changelist):
        # Skip the default Django "All" entry (None) so the explicit 'all'
        # lookup is the only way to see everything, and so the chosen default
        # shows as selected when no query param is set.
        current = self.value() if self.value() is not None else self.default_value
        for lookup, title in self.lookup_choices:
            yield {
                "selected": current == lookup,
                "query_string": changelist.get_query_string({self.parameter_name: lookup}),
                "display": title,
            }

    def queryset(self, request, queryset):
        field = self.date_field
        if not field:
            return queryset
        now = timezone.now()
        dayago = now - timedelta(days=1)
        value = self.value() or self.default_value
        if value == "recent":
            return queryset.filter(**{f"{field}__gte": dayago}).order_by(field, "name")
        if value == "upcoming":
            return queryset.filter(**{f"{field}__gte": now}).order_by(field, "name")
        if value == "previous":
            return queryset.filter(**{f"{field}__lte": now}).order_by(f"-{field}", "name")
        return queryset.order_by(f"-{field}", "name")


class LaunchDateListFilter(_DateRangeFilter):
    date_field = "net"


class EventDateListFilter(_DateRangeFilter):
    date_field = "date"


class LaunchNetYearFilter(SimpleListFilter):
    title = "year"
    parameter_name = "year"

    def lookups(self, request, model_admin):
        from django.db.models.functions import ExtractYear

        years = (
            model_admin.get_queryset(request)
            .annotate(year=ExtractYear("net"))
            .values_list("year", flat=True)
            .distinct()
            .order_by("-year")
        )
        return [(y, str(y)) for y in years if y is not None]

    def queryset(self, request, queryset):
        if self.value():
            return queryset.filter(net__year=self.value())
        return queryset


LAUNCH_READONLY = (
    "id",
    "slug",
    "url",
    "provider_id",
    "provider_type",
    "provider_country_code",
    "provider_logo_url",
    "rocket_config_id",
    "rocket_family",
    "rocket_variant",
    "pad_id",
    "pad_latitude",
    "pad_longitude",
    "pad_state",
    "location_id",
    "location_country_code",
    "location_region",
    "mission_description",
    "orbit_id",
    "mission_type_id",
    "image_thumbnail_url",
    "orbital_launch_attempt_count",
    "pad_launch_attempt_count",
    "provider_launch_attempt_count",
    "programs",
    "vid_urls",
    "info_urls",
    "mission_patches",
    "updates",
    "ll_updated_at",
    "synced_at",
    "created_at",
    "updated_at",
)


@admin.register(Launch)
class LaunchAdmin(admin.ModelAdmin):
    list_display = (
        "name",
        "net_formatted",
        "net_precision_name",
        "status_formatted",
        "provider_name",
        "rocket_full_name",
        "orbit_formatted",
        "has_img",
        "has_vid",
        "has_info",
        "has_patch",
        "program_formatted",
        "location_name",
        "is_crewed",
        "webcast_live",
    )
    list_filter = (
        LaunchDateListFilter,
        LaunchNetYearFilter,
        "status_id",
        "is_crewed",
        "webcast_live",
        "location_region",
        "orbit_abbrev",
    )
    search_fields = ("name", "provider_name", "rocket_full_name", "location_name", "mission_name")
    readonly_fields = LAUNCH_READONLY
    ordering = ("-net",)
    list_per_page = 50

    def net_formatted(self, launch):
        if not launch.net:
            return "—"
        if launch.net.second == 0 and launch.net.minute == 0 and launch.net.hour == 0:
            net_str = launch.net.strftime("%b %d, %Y – midnight")
        elif launch.net.second == 0:
            net_str = launch.net.strftime("%b %d, %Y – %H:%M")
        else:
            net_str = launch.net.strftime("%b %d, %Y – %H:%M:%S")
        precision = launch.net_precision_name or "unknown"
        return format_html('<div title="Precision: {}">{}</div>', precision, net_str)

    net_formatted.short_description = "NET (UTC)"
    net_formatted.admin_order_field = "net"

    def status_formatted(self, launch):
        colors = {
            1: "LawnGreen",  # Go
            2: "Salmon",  # TBD
            3: "YellowGreen",  # Success
            4: "Tomato",  # Failure
            5: "SkyBlue",  # Hold
            6: "PaleTurquoise",  # In Flight
            7: "Pink",  # Partial Failure
            8: "PeachPuff",  # TBC
            9: "#3385D6",  # Payload Deployed
        }
        color = colors.get(launch.status_id, "#ccc")
        return format_html(
            '<div title="{}" style="padding:5px;border-radius:5px;text-align:center;'
            'background:{};color:black">{}</div>',
            launch.status_name,
            color,
            launch.status_abbrev,
        )

    status_formatted.short_description = "Status"
    status_formatted.admin_order_field = "status_id"

    def has_info(self, launch):
        return bool(launch.info_urls)

    has_info.short_description = format_html('<div title="Has at least one InfoURL">Info</div>')
    has_info.boolean = True

    def has_vid(self, launch):
        return bool(launch.vid_urls)

    has_vid.short_description = format_html('<div title="Has at least one VideoURL">Vid</div>')
    has_vid.boolean = True

    def has_patch(self, launch):
        if not launch.mission_patches:
            return "None"
        first = launch.mission_patches[0]
        image_url = first.get("image_url", "") if isinstance(first, dict) else ""
        if image_url:
            return format_html(
                '<img loading="lazy" src="{}" height=25 style="border-radius:3px"/>',
                image_url,
            )
        return "—"

    has_patch.short_description = format_html('<div title="Has a mission patch">Patch</div>')

    def has_img(self, launch):
        return bool(launch.image_url)

    has_img.short_description = format_html('<div title="Has a custom image">IMG</div>')
    has_img.boolean = True

    def program_formatted(self, launch):
        if not launch.programs:
            return "—"
        names = ", ".join(p.get("name", "?") for p in launch.programs if isinstance(p, dict))
        return format_html(
            '<div title="{}" style="text-align:center">{}</div>',
            names,
            len(launch.programs),
        )

    program_formatted.short_description = format_html('<div title="Programs">PGM</div>')

    def orbit_formatted(self, launch):
        if not launch.orbit_abbrev:
            return format_html('<div style="padding:5px;border-radius:5px;background:Salmon;color:black">—</div>')
        return format_html(
            '<div title="{}">{}</div>',
            launch.orbit_name or launch.orbit_abbrev,
            launch.orbit_abbrev,
        )

    orbit_formatted.short_description = "Orbit"
    orbit_formatted.admin_order_field = "orbit_abbrev"

    fieldsets = (
        ("Identity", {"fields": ("id", "slug", "name", "url")}),
        (
            "Status & Timing",
            {
                "fields": (
                    "status_id",
                    "status_name",
                    "status_abbrev",
                    "net",
                    "window_start",
                    "window_end",
                    "net_precision_name",
                )
            },
        ),
        (
            "Provider",
            {"fields": ("provider_id", "provider_name", "provider_type", "provider_country_code", "provider_logo_url")},
        ),
        ("Rocket", {"fields": ("rocket_config_id", "rocket_full_name", "rocket_family", "rocket_variant")}),
        (
            "Pad & Location",
            {
                "fields": (
                    "pad_id",
                    "pad_name",
                    "pad_latitude",
                    "pad_longitude",
                    "pad_state",
                    "location_id",
                    "location_name",
                    "location_country_code",
                    "location_region",
                )
            },
        ),
        (
            "Mission",
            {
                "fields": (
                    "mission_name",
                    "mission_description",
                    "mission_type",
                    "mission_type_id",
                    "orbit_name",
                    "orbit_abbrev",
                    "orbit_id",
                )
            },
        ),
        ("Media", {"fields": ("image_url", "image_thumbnail_url", "infographic_url")}),
        ("Flags", {"fields": ("is_crewed", "webcast_live")}),
        (
            "Counters",
            {"fields": ("orbital_launch_attempt_count", "pad_launch_attempt_count", "provider_launch_attempt_count")},
        ),
        (
            "JSONB Data",
            {"fields": ("programs", "vid_urls", "info_urls", "mission_patches", "updates"), "classes": ("collapse",)},
        ),
        (
            "Sync Metadata",
            {"fields": ("ll_updated_at", "synced_at", "created_at", "updated_at"), "classes": ("collapse",)},
        ),
    )


# ─── Events ───────────────────────────────────────────────────────────────────


@admin.register(Event)
class EventAdmin(admin.ModelAdmin):
    list_display = ("name", "type_name", "date", "location")
    list_filter = (EventDateListFilter, "type_id")
    search_fields = ("name", "description", "location")
    readonly_fields = (
        "id",
        "launches",
        "programs",
        "updates",
        "ll_updated_at",
        "synced_at",
        "created_at",
        "updated_at",
    )
    ordering = ("-date",)


# ─── Agencies ─────────────────────────────────────────────────────────────────


@admin.register(Agency)
class AgencyAdmin(admin.ModelAdmin):
    list_display = ("name", "abbrev", "country_code", "type_name", "total_launch_count", "featured")
    list_filter = ("type_id", "featured")
    search_fields = ("name", "abbrev", "country_code")
    readonly_fields = ("id", "synced_at", "created_at", "updated_at")
    ordering = ("name",)


# ─── Vehicles ─────────────────────────────────────────────────────────────────


@admin.register(Vehicle)
class VehicleAdmin(admin.ModelAdmin):
    list_display = ("full_name", "family", "manufacturer_name", "total_launch_count", "active", "reusable")
    list_filter = ("active", "reusable", "is_placeholder")
    search_fields = ("full_name", "name", "family", "manufacturer_name")
    readonly_fields = ("id", "synced_at", "created_at", "updated_at")
    ordering = ("name",)


# ─── Astronauts ───────────────────────────────────────────────────────────────


@admin.register(Astronaut)
class AstronautAdmin(admin.ModelAdmin):
    list_display = ("name", "nationality", "agency_name", "status_name", "flights_count", "in_space")
    list_filter = ("status_id", "in_space")
    search_fields = ("name", "nationality", "agency_name")
    readonly_fields = ("id", "synced_at", "created_at", "updated_at")
    ordering = ("name",)


# ─── Space Stations ───────────────────────────────────────────────────────────


@admin.register(SpaceStation)
class SpaceStationAdmin(admin.ModelAdmin):
    list_display = ("name", "status_name", "type_name", "orbit", "founded")
    list_filter = ("status_id", "type_id")
    search_fields = ("name", "orbit")
    readonly_fields = (
        "id",
        "owners",
        "active_expeditions",
        "docking_locations",
        "synced_at",
        "created_at",
        "updated_at",
    )
    ordering = ("name",)


# ─── Programs ─────────────────────────────────────────────────────────────────


@admin.register(Program)
class ProgramAdmin(admin.ModelAdmin):
    list_display = ("name", "type_name", "start_date", "end_date")
    list_filter = ("type_id",)
    search_fields = ("name", "description")
    readonly_fields = ("id", "agencies", "mission_patches", "synced_at", "created_at", "updated_at")
    ordering = ("name",)


# ─── Locations ────────────────────────────────────────────────────────────────


@admin.register(Location)
class LocationAdmin(admin.ModelAdmin):
    list_display = ("name", "country_code", "timezone_name", "total_launch_count", "active")
    list_filter = ("active", "country_code")
    search_fields = ("name", "country_code")
    readonly_fields = ("id", "pads", "synced_at", "created_at", "updated_at")
    ordering = ("name",)


# ─── Launchers ────────────────────────────────────────────────────────────────


@admin.register(Launcher)
class LauncherAdmin(admin.ModelAdmin):
    list_display = (
        "launcher_config_full_name",
        "serial_number",
        "status",
        "flights_count",
        "successful_landings",
        "flight_proven",
    )
    list_filter = ("flight_proven", "status")
    search_fields = ("serial_number", "launcher_config_name", "launcher_config_full_name")
    readonly_fields = ("id", "synced_at", "created_at", "updated_at")
    ordering = ("launcher_config_name", "serial_number")


# ─── Spacecraft ───────────────────────────────────────────────────────────────


@admin.register(Spacecraft)
class SpacecraftAdmin(admin.ModelAdmin):
    list_display = ("name", "serial_number", "status_name", "spacecraft_config_name", "in_space", "flights_count")
    list_filter = ("status_id", "in_space", "is_placeholder")
    search_fields = ("name", "serial_number", "spacecraft_config_name")
    readonly_fields = ("id", "synced_at", "created_at", "updated_at")
    ordering = ("name",)


# ─── Spacecraft Configurations ────────────────────────────────────────────────


@admin.register(SpacecraftConfiguration)
class SpacecraftConfigurationAdmin(admin.ModelAdmin):
    list_display = ("name", "type_name", "agency_name", "in_use")
    list_filter = ("in_use", "type_id")
    search_fields = ("name", "agency_name")
    readonly_fields = ("id", "synced_at", "created_at", "updated_at")
    ordering = ("name",)


# ─── Updates ──────────────────────────────────────────────────────────────────


@admin.register(Update)
class UpdateAdmin(admin.ModelAdmin):
    list_display = ("id", "created_by", "created_on", "launch_id", "event_id")
    list_filter = ()
    search_fields = ("comment", "created_by")
    readonly_fields = ("id", "synced_at", "created_at", "updated_at")
    ordering = ("-created_on",)
    date_hierarchy = "created_on"


# ─── Expeditions ──────────────────────────────────────────────────────────────


@admin.register(Expedition)
class ExpeditionAdmin(admin.ModelAdmin):
    list_display = ("name", "space_station_name", "start_date", "end_date")
    list_filter = ("space_station_id",)
    search_fields = ("name", "space_station_name")
    readonly_fields = ("id", "mission_patches", "spacewalks", "synced_at", "created_at", "updated_at")
    ordering = ("-start_date",)


# ─── Config Tables ────────────────────────────────────────────────────────────


@admin.register(ConfigLaunchStatus)
class ConfigLaunchStatusAdmin(admin.ModelAdmin):
    list_display = ("id", "abbrev", "name", "description")
    readonly_fields = ("id", "name", "abbrev", "description")

    def has_add_permission(self, request):
        return False

    def has_delete_permission(self, request, obj=None):
        return False


@admin.register(ConfigOrbit)
class ConfigOrbitAdmin(admin.ModelAdmin):
    list_display = ("id", "abbrev", "name")
    readonly_fields = ("id", "name", "abbrev")

    def has_add_permission(self, request):
        return False

    def has_delete_permission(self, request, obj=None):
        return False
