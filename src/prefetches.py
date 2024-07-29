from api.models import AstronautFlight
from django.db.models import Prefetch


def get_prefetched_launch_queryset(queryset, detailed=False):
    queryset = (
        queryset.select_related("status")
        .prefetch_related("info_urls")
        .prefetch_related("vid_urls")
        .select_related("mission")
        .select_related("mission__orbit")
        .select_related("mission__mission_type")
        .prefetch_related("mission_patches")
        .select_related("pad")
        .select_related("pad__location")
        .prefetch_related("pad__location__landing_location")
        .select_related("rocket")
        .prefetch_related("rocket__firststage")
        .select_related("rocket__configuration")
        .select_related("rocket__configuration__manufacturer")
        .prefetch_related("program")
        .prefetch_related("program__agency")
        .prefetch_related("program__mission_patches")
        .select_related("changed_by")
        .prefetch_related("updates__created_by")
        .prefetch_related("updates__created_by__tsdstaff")
        .select_related("launch_service_provider")
        .select_related("net_precision")
    )

    if detailed:
        queryset = (
            queryset.prefetch_related("rocket__configuration__program")
            .prefetch_related("rocket__configuration__program__agency")
            .prefetch_related("rocket__firststage__type")
            .prefetch_related("rocket__firststage__landing")
            .prefetch_related("rocket__firststage__landing__landing_type")
            .prefetch_related("rocket__firststage__landing__landing_location")
            .prefetch_related("rocket__firststage__landing__landing_location__location")
            .prefetch_related("rocket__firststage__launcher")
            .prefetch_related("rocket__firststage__previous_flight")
            .prefetch_related("rocket__spacecraftflight")
            .prefetch_related(
                Prefetch(
                    "rocket__spacecraftflight__launch_crew",
                    queryset=AstronautFlight.objects.select_related("role")
                    .select_related("astronaut")
                    .select_related("astronaut__status")
                    .select_related("astronaut__type")
                    .select_related("astronaut__agency"),
                )
            )
            .prefetch_related(
                Prefetch(
                    "rocket__spacecraftflight__onboard_crew",
                    queryset=AstronautFlight.objects.select_related("role")
                    .select_related("astronaut")
                    .select_related("astronaut__status")
                    .select_related("astronaut__type")
                    .select_related("astronaut__agency"),
                )
            )
            .prefetch_related(
                Prefetch(
                    "rocket__spacecraftflight__landing_crew",
                    queryset=AstronautFlight.objects.select_related("role")
                    .select_related("astronaut")
                    .select_related("astronaut__status")
                    .select_related("astronaut__type")
                    .select_related("astronaut__agency"),
                )
            )
            .prefetch_related("rocket__spacecraftflight__landing")
            .prefetch_related("rocket__spacecraftflight__spacecraft")
            .prefetch_related("rocket__spacecraftflight__spacecraft__spacecraft_config")
            .prefetch_related("rocket__spacecraftflight__spacecraft__spacecraft_config__type")
            .prefetch_related("rocket__spacecraftflight__spacecraft__spacecraft_config__agency")
            .prefetch_related("rocket__spacecraftflight__spacecraft__status")
            .prefetch_related("rocket__spacecraftflight__landing__landing_type")
            .prefetch_related("rocket__spacecraftflight__landing__landing_location")
            .prefetch_related("rocket__spacecraftflight__landing__landing_location__location")
            .prefetch_related("rocket__spacecraftflight__docking_events_chaser")
            .prefetch_related("mission__vid_urls")
            .prefetch_related("mission__info_urls")
            .prefetch_related("mission__agencies")
            .prefetch_related("info_urls__language")
            .prefetch_related("info_urls__type")
            .prefetch_related("vid_urls__language")
            .prefetch_related("vid_urls__type")
            .prefetch_related("program__mission_patches__agency")
            .prefetch_related("mission_patches__agency")
        )

    return queryset
