"""
Unmanaged Django models for the SpaceLaunchNow Go API database.

All models use managed = False so Django never creates, alters, or drops these
tables. The schema is owned by the Go API's golang-migrate system.

The 'sln_api' database alias is used for all reads/writes via SLNApiRouter.
"""

import uuid

from django.db import models

# ─── Sync Control ─────────────────────────────────────────────────────────────


class SyncJobConfig(models.Model):
    """
    Controls whether each sync type runs in the Go worker.
    Toggle enabled/disabled from the Django admin without restarting the worker.
    Changes take effect within ~60 seconds (worker cache TTL).
    """

    sync_type = models.TextField(primary_key=True)
    enabled = models.BooleanField(default=True)
    note = models.TextField(blank=True, null=True)
    updated_at = models.DateTimeField(auto_now=False)

    class Meta:
        managed = False
        db_table = "sync_config"
        app_label = "sln_api"
        ordering = ["sync_type"]
        verbose_name = "Sync Job Config"
        verbose_name_plural = "Sync Job Configs"

    def __str__(self):
        status = "✅" if self.enabled else "⛔"
        return f"{status} {self.sync_type}"


# ─── Config / Lookup Tables ───────────────────────────────────────────────────


class ConfigLaunchStatus(models.Model):
    id = models.IntegerField(primary_key=True)
    name = models.TextField()
    abbrev = models.TextField()
    description = models.TextField(blank=True, null=True)

    class Meta:
        managed = False
        db_table = "config_launch_status"
        app_label = "sln_api"
        ordering = ["id"]
        verbose_name = "Launch Status"
        verbose_name_plural = "Launch Statuses"

    def __str__(self):
        return f"{self.abbrev} — {self.name}"


class ConfigOrbit(models.Model):
    id = models.IntegerField(primary_key=True)
    name = models.TextField()
    abbrev = models.TextField()

    class Meta:
        managed = False
        db_table = "config_orbit"
        app_label = "sln_api"
        ordering = ["name"]
        verbose_name = "Orbit"
        verbose_name_plural = "Orbits"

    def __str__(self):
        return f"{self.abbrev} — {self.name}"


# ─── Launches ─────────────────────────────────────────────────────────────────


class Launch(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4)
    slug = models.TextField()
    name = models.TextField()
    url = models.TextField(blank=True, null=True)

    # Timing
    net = models.DateTimeField(blank=True, null=True)
    window_start = models.DateTimeField(blank=True, null=True)
    window_end = models.DateTimeField(blank=True, null=True)
    net_precision_name = models.TextField(blank=True, null=True)

    # Status
    status_id = models.IntegerField(default=2)
    status_name = models.TextField(default="To Be Determined")
    status_abbrev = models.TextField(default="TBD")

    # Provider (denormalized)
    provider_id = models.IntegerField(blank=True, null=True)
    provider_name = models.TextField(blank=True, null=True)
    provider_type = models.TextField(blank=True, null=True)
    provider_country_code = models.TextField(blank=True, null=True)
    provider_logo_url = models.TextField(blank=True, null=True)

    # Rocket (denormalized)
    rocket_config_id = models.IntegerField(blank=True, null=True)
    rocket_full_name = models.TextField(blank=True, null=True)
    rocket_family = models.TextField(blank=True, null=True)
    rocket_variant = models.TextField(blank=True, null=True)

    # Pad / Location (denormalized)
    pad_id = models.IntegerField(blank=True, null=True)
    pad_name = models.TextField(blank=True, null=True)
    pad_latitude = models.FloatField(blank=True, null=True)
    pad_longitude = models.FloatField(blank=True, null=True)
    pad_state = models.CharField(max_length=2, blank=True, null=True)
    location_id = models.IntegerField(blank=True, null=True)
    location_name = models.TextField(blank=True, null=True)
    location_country_code = models.TextField(blank=True, null=True)
    location_region = models.TextField(blank=True, null=True)

    # Mission (denormalized)
    mission_name = models.TextField(blank=True, null=True)
    mission_description = models.TextField(blank=True, null=True)
    mission_type = models.TextField(blank=True, null=True)
    orbit_name = models.TextField(blank=True, null=True)
    orbit_abbrev = models.TextField(blank=True, null=True)
    orbit_id = models.IntegerField(blank=True, null=True)
    mission_type_id = models.IntegerField(blank=True, null=True)

    # Media
    image_url = models.TextField(blank=True, null=True)
    image_thumbnail_url = models.TextField(blank=True, null=True)
    infographic_url = models.TextField(blank=True, null=True)

    # Flags
    is_crewed = models.BooleanField(default=False)
    webcast_live = models.BooleanField(default=False)

    # Counters
    orbital_launch_attempt_count = models.IntegerField(blank=True, null=True)
    pad_launch_attempt_count = models.IntegerField(blank=True, null=True)
    provider_launch_attempt_count = models.IntegerField(blank=True, null=True)

    # JSONB
    programs = models.JSONField(default=list)
    vid_urls = models.JSONField(default=list)
    info_urls = models.JSONField(default=list)
    mission_patches = models.JSONField(default=list)
    updates = models.JSONField(default=list)

    # Sync metadata
    ll_updated_at = models.DateTimeField(blank=True, null=True)
    synced_at = models.DateTimeField()
    created_at = models.DateTimeField()
    updated_at = models.DateTimeField()

    class Meta:
        managed = False
        db_table = "launches"
        app_label = "sln_api"
        ordering = ["-net"]
        verbose_name = "Launch"
        verbose_name_plural = "Launches"

    def __str__(self):
        net_str = self.net.strftime("%Y-%m-%d") if self.net else "TBD"
        return f"{self.name} ({self.status_abbrev}) — {net_str}"


# ─── Events ───────────────────────────────────────────────────────────────────


class Event(models.Model):
    id = models.IntegerField(primary_key=True)
    name = models.TextField()
    slug = models.TextField(blank=True, null=True)
    type_id = models.IntegerField(blank=True, null=True)
    type_name = models.TextField(blank=True, null=True)
    description = models.TextField(blank=True, null=True)
    date = models.DateTimeField(blank=True, null=True)
    location = models.TextField(blank=True, null=True)
    news_url = models.TextField(blank=True, null=True)
    video_url = models.TextField(blank=True, null=True)
    image_url = models.TextField(blank=True, null=True)
    feature_image_url = models.TextField(blank=True, null=True)

    launches = models.JSONField(default=list)
    programs = models.JSONField(default=list)
    updates = models.JSONField(default=list)

    ll_updated_at = models.DateTimeField(blank=True, null=True)
    synced_at = models.DateTimeField()
    created_at = models.DateTimeField()
    updated_at = models.DateTimeField()

    class Meta:
        managed = False
        db_table = "events"
        app_label = "sln_api"
        ordering = ["-date"]
        verbose_name = "Event"
        verbose_name_plural = "Events"

    def __str__(self):
        date_str = self.date.strftime("%Y-%m-%d") if self.date else "TBD"
        return f"{self.name} — {date_str}"


# ─── Agencies ─────────────────────────────────────────────────────────────────


class Agency(models.Model):
    id = models.IntegerField(primary_key=True)
    name = models.TextField()
    abbrev = models.TextField(blank=True, null=True)
    type_id = models.IntegerField(blank=True, null=True)
    type_name = models.TextField(blank=True, null=True)
    country_code = models.TextField(blank=True, null=True)
    description = models.TextField(blank=True, null=True)
    administrator = models.TextField(blank=True, null=True)
    founding_year = models.IntegerField(blank=True, null=True)
    total_launch_count = models.IntegerField(default=0)
    successful_launches = models.IntegerField(default=0)
    failed_launches = models.IntegerField(default=0)
    pending_launches = models.IntegerField(default=0)
    consecutive_successful_launches = models.IntegerField(default=0)
    logo_url = models.TextField(blank=True, null=True)
    image_url = models.TextField(blank=True, null=True)
    wiki_url = models.TextField(blank=True, null=True)
    info_url = models.TextField(blank=True, null=True)
    featured = models.BooleanField(default=False)

    synced_at = models.DateTimeField()
    created_at = models.DateTimeField()
    updated_at = models.DateTimeField()

    class Meta:
        managed = False
        db_table = "agencies"
        app_label = "sln_api"
        ordering = ["name"]
        verbose_name = "Agency"
        verbose_name_plural = "Agencies"

    def __str__(self):
        return f"{self.name} ({self.country_code or '?'})"


# ─── Vehicles (Launcher Configs) ──────────────────────────────────────────────


class Vehicle(models.Model):
    id = models.IntegerField(primary_key=True)
    name = models.TextField()
    full_name = models.TextField()
    slug = models.TextField(blank=True, null=True)
    family = models.TextField(blank=True, null=True)
    variant = models.TextField(blank=True, null=True)
    manufacturer_id = models.IntegerField(blank=True, null=True)
    manufacturer_name = models.TextField(blank=True, null=True)
    manufacturer_country_code = models.TextField(blank=True, null=True)
    description = models.TextField(blank=True, null=True)
    image_url = models.TextField(blank=True, null=True)
    maiden_flight = models.DateField(blank=True, null=True)
    total_launch_count = models.IntegerField(default=0)
    successful_launches = models.IntegerField(default=0)
    failed_launches = models.IntegerField(default=0)
    pending_launches = models.IntegerField(default=0)
    consecutive_successful_launches = models.IntegerField(default=0)
    active = models.BooleanField(default=True)
    reusable = models.BooleanField(default=False)
    is_placeholder = models.BooleanField(default=False)

    synced_at = models.DateTimeField()
    created_at = models.DateTimeField()
    updated_at = models.DateTimeField()

    class Meta:
        managed = False
        db_table = "vehicles"
        app_label = "sln_api"
        ordering = ["name"]
        verbose_name = "Vehicle (Launcher Config)"
        verbose_name_plural = "Vehicles (Launcher Configs)"

    def __str__(self):
        return self.full_name


# ─── Astronauts ───────────────────────────────────────────────────────────────


class Astronaut(models.Model):
    id = models.IntegerField(primary_key=True)
    name = models.TextField()
    slug = models.TextField(blank=True, null=True)
    status_id = models.IntegerField(blank=True, null=True)
    status_name = models.TextField(blank=True, null=True)
    type_id = models.IntegerField(blank=True, null=True)
    type_name = models.TextField(blank=True, null=True)
    agency_id = models.IntegerField(blank=True, null=True)
    agency_name = models.TextField(blank=True, null=True)
    agency_country_code = models.TextField(blank=True, null=True)
    nationality = models.TextField(blank=True, null=True)
    bio = models.TextField(blank=True, null=True)
    profile_image_url = models.TextField(blank=True, null=True)
    flights_count = models.IntegerField(default=0)
    landings_count = models.IntegerField(default=0)
    spacewalks_count = models.IntegerField(default=0)
    last_flight = models.DateTimeField(blank=True, null=True)
    first_flight = models.DateTimeField(blank=True, null=True)
    in_space = models.BooleanField(default=False)
    date_of_birth = models.DateField(blank=True, null=True)
    date_of_death = models.DateField(blank=True, null=True)

    synced_at = models.DateTimeField()
    created_at = models.DateTimeField()
    updated_at = models.DateTimeField()

    class Meta:
        managed = False
        db_table = "astronauts"
        app_label = "sln_api"
        ordering = ["name"]
        verbose_name = "Astronaut"
        verbose_name_plural = "Astronauts"

    def __str__(self):
        return self.name


# ─── Space Stations ───────────────────────────────────────────────────────────


class SpaceStation(models.Model):
    id = models.IntegerField(primary_key=True)
    name = models.TextField()
    slug = models.TextField(blank=True, null=True)
    status_id = models.IntegerField(blank=True, null=True)
    status_name = models.TextField(blank=True, null=True)
    type_id = models.IntegerField(blank=True, null=True)
    type_name = models.TextField(blank=True, null=True)
    founded = models.DateField(blank=True, null=True)
    deorbited = models.DateField(blank=True, null=True)
    description = models.TextField(blank=True, null=True)
    orbit = models.TextField(blank=True, null=True)
    image_url = models.TextField(blank=True, null=True)

    owners = models.JSONField(default=list)
    active_expeditions = models.JSONField(default=list)
    docking_locations = models.JSONField(default=list)

    synced_at = models.DateTimeField()
    created_at = models.DateTimeField()
    updated_at = models.DateTimeField()

    class Meta:
        managed = False
        db_table = "space_stations"
        app_label = "sln_api"
        ordering = ["name"]
        verbose_name = "Space Station"
        verbose_name_plural = "Space Stations"

    def __str__(self):
        return self.name


# ─── Programs ─────────────────────────────────────────────────────────────────


class Program(models.Model):
    id = models.IntegerField(primary_key=True)
    name = models.TextField()
    description = models.TextField(blank=True, null=True)
    image_url = models.TextField(blank=True, null=True)
    start_date = models.DateTimeField(blank=True, null=True)
    end_date = models.DateTimeField(blank=True, null=True)
    info_url = models.TextField(blank=True, null=True)
    wiki_url = models.TextField(blank=True, null=True)
    type_id = models.IntegerField(blank=True, null=True)
    type_name = models.TextField(blank=True, null=True)

    agencies = models.JSONField(default=list)
    mission_patches = models.JSONField(default=list)

    synced_at = models.DateTimeField()
    created_at = models.DateTimeField()
    updated_at = models.DateTimeField()

    class Meta:
        managed = False
        db_table = "programs"
        app_label = "sln_api"
        ordering = ["name"]
        verbose_name = "Program"
        verbose_name_plural = "Programs"

    def __str__(self):
        return self.name


# ─── Locations ────────────────────────────────────────────────────────────────


class Location(models.Model):
    id = models.IntegerField(primary_key=True)
    name = models.TextField(blank=True, null=True)
    country_code = models.TextField(blank=True, null=True)
    description = models.TextField(blank=True, null=True)
    image_url = models.TextField(blank=True, null=True)
    map_image_url = models.TextField(blank=True, null=True)
    longitude = models.FloatField(blank=True, null=True)
    latitude = models.FloatField(blank=True, null=True)
    timezone_name = models.TextField(blank=True, null=True)
    total_launch_count = models.IntegerField(blank=True, null=True)
    total_landing_count = models.IntegerField(blank=True, null=True)
    active = models.BooleanField(default=True)

    pads = models.JSONField(default=list)

    synced_at = models.DateTimeField()
    created_at = models.DateTimeField()
    updated_at = models.DateTimeField()

    class Meta:
        managed = False
        db_table = "locations"
        app_label = "sln_api"
        ordering = ["name"]
        verbose_name = "Location"
        verbose_name_plural = "Locations"

    def __str__(self):
        return f"{self.name} ({self.country_code or '?'})"


# ─── Launchers (Booster Instances) ────────────────────────────────────────────


class Launcher(models.Model):
    id = models.IntegerField(primary_key=True)
    serial_number = models.TextField(blank=True, null=True)
    status = models.TextField(blank=True, null=True)
    details = models.TextField(blank=True, null=True)
    flight_proven = models.BooleanField(default=False)
    image_url = models.TextField(blank=True, null=True)
    flights_count = models.IntegerField(default=0)
    attempted_landings = models.IntegerField(default=0)
    successful_landings = models.IntegerField(default=0)
    last_launch_date = models.DateTimeField(blank=True, null=True)
    first_launch_date = models.DateTimeField(blank=True, null=True)
    launcher_config_id = models.IntegerField(blank=True, null=True)
    launcher_config_name = models.TextField(blank=True, null=True)
    launcher_config_full_name = models.TextField(blank=True, null=True)

    synced_at = models.DateTimeField()
    created_at = models.DateTimeField()
    updated_at = models.DateTimeField()

    class Meta:
        managed = False
        db_table = "launchers"
        app_label = "sln_api"
        ordering = ["launcher_config_name", "serial_number"]
        verbose_name = "Launcher (Booster)"
        verbose_name_plural = "Launchers (Boosters)"

    def __str__(self):
        name = self.launcher_config_full_name or self.launcher_config_name or "Unknown"
        serial = self.serial_number or f"#{self.id}"
        return f"{name} — {serial}"


# ─── Spacecraft ───────────────────────────────────────────────────────────────


class Spacecraft(models.Model):
    id = models.IntegerField(primary_key=True)
    name = models.TextField()
    serial_number = models.TextField(blank=True, null=True)
    is_placeholder = models.BooleanField(default=False)
    in_space = models.BooleanField(default=False)
    status_id = models.IntegerField(blank=True, null=True)
    status_name = models.TextField(blank=True, null=True)
    description = models.TextField(blank=True, null=True)
    image_url = models.TextField(blank=True, null=True)
    flights_count = models.IntegerField(default=0)
    mission_ends_count = models.IntegerField(default=0)
    spacecraft_config_id = models.IntegerField(blank=True, null=True)
    spacecraft_config_name = models.TextField(blank=True, null=True)

    synced_at = models.DateTimeField()
    created_at = models.DateTimeField()
    updated_at = models.DateTimeField()

    class Meta:
        managed = False
        db_table = "spacecraft"
        app_label = "sln_api"
        ordering = ["name"]
        verbose_name = "Spacecraft"
        verbose_name_plural = "Spacecraft"

    def __str__(self):
        serial = self.serial_number or f"#{self.id}"
        return f"{self.name} — {serial}"


# ─── Spacecraft Configurations ────────────────────────────────────────────────


class SpacecraftConfiguration(models.Model):
    id = models.IntegerField(primary_key=True)
    name = models.TextField()
    type_id = models.IntegerField(blank=True, null=True)
    type_name = models.TextField(blank=True, null=True)
    agency_id = models.IntegerField(blank=True, null=True)
    agency_name = models.TextField(blank=True, null=True)
    in_use = models.BooleanField(default=False)
    image_url = models.TextField(blank=True, null=True)

    synced_at = models.DateTimeField()
    created_at = models.DateTimeField()
    updated_at = models.DateTimeField()

    class Meta:
        managed = False
        db_table = "spacecraft_configurations"
        app_label = "sln_api"
        ordering = ["name"]
        verbose_name = "Spacecraft Configuration"
        verbose_name_plural = "Spacecraft Configurations"

    def __str__(self):
        agency = f" ({self.agency_name})" if self.agency_name else ""
        return f"{self.name}{agency}"


# ─── Updates ──────────────────────────────────────────────────────────────────


class Update(models.Model):
    id = models.IntegerField(primary_key=True)
    profile_image = models.TextField(blank=True, null=True)
    comment = models.TextField(blank=True, null=True)
    info_url = models.TextField(blank=True, null=True)
    created_by = models.TextField(blank=True, null=True)
    created_on = models.DateTimeField(blank=True, null=True)
    launch_id = models.UUIDField(blank=True, null=True)
    event_id = models.IntegerField(blank=True, null=True)

    synced_at = models.DateTimeField()
    created_at = models.DateTimeField()
    updated_at = models.DateTimeField()

    class Meta:
        managed = False
        db_table = "updates"
        app_label = "sln_api"
        ordering = ["-created_on"]
        verbose_name = "Update"
        verbose_name_plural = "Updates"

    def __str__(self):
        by = self.created_by or "Unknown"
        date_str = self.created_on.strftime("%Y-%m-%d") if self.created_on else "?"
        preview = (self.comment or "")[:60]
        return f"[{date_str}] {by}: {preview}"


# ─── Expeditions ──────────────────────────────────────────────────────────────


class Expedition(models.Model):
    id = models.IntegerField(primary_key=True)
    name = models.TextField(blank=True, null=True)
    start_date = models.DateTimeField(blank=True, null=True)
    end_date = models.DateTimeField(blank=True, null=True)
    space_station_id = models.IntegerField(blank=True, null=True)
    space_station_name = models.TextField(blank=True, null=True)
    space_station_image_url = models.TextField(blank=True, null=True)

    mission_patches = models.JSONField(default=list)
    spacewalks = models.JSONField(default=list)

    synced_at = models.DateTimeField()
    created_at = models.DateTimeField()
    updated_at = models.DateTimeField()

    class Meta:
        managed = False
        db_table = "expeditions"
        app_label = "sln_api"
        ordering = ["-start_date"]
        verbose_name = "Expedition"
        verbose_name_plural = "Expeditions"

    def __str__(self):
        return self.name or f"Expedition #{self.id}"
