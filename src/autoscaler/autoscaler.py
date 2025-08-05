"""
Autoscaler for SpaceLaunchNow - Kubernetes node pool management.

This module provides comprehensive logging for:
- Autoscaler initialization and configuration
- Launch and event detection with weighting calculations
- Worker count calculations and scaling decisions
- Node pool and KEDA scaling operations
- Performance monitoring and debugging information
"""

import datetime as dtime
import logging

import pytz
from api.models import Events, Launch

from autoscaler.digitalocean_helper import DigitalOceanHelper
from autoscaler.models import AutoscalerSettings

logger = logging.getLogger(__name__)


def check_autoscaler():
    logger.info("Starting autoscaler check")

    # First initialize helper classes.
    logger.debug("Initializing DigitalOcean helper")
    do = DigitalOceanHelper()

    # Get Autoscaler settings and make sure the latest worker node count is correct
    logger.debug("Loading autoscaler settings")
    autoscaler_settings = AutoscalerSettings.load()

    # Get current node pool minimum and update settings
    current_min_nodes = do.get_node_pool_min()
    if current_min_nodes != autoscaler_settings.current_workers:
        logger.info(f"Updating current_workers from {autoscaler_settings.current_workers} to {current_min_nodes}")
        autoscaler_settings.current_workers = current_min_nodes
        autoscaler_settings.save()
    else:
        logger.debug(f"Current min nodes unchanged: {current_min_nodes}")

    logger.info(
        f"Autoscaler configuration - Enabled: {autoscaler_settings.enabled}, "
        f"Current Workers: {autoscaler_settings.current_workers}, "
        f"Max Workers: {autoscaler_settings.max_workers}, "
        f"Custom Count: {autoscaler_settings.custom_worker_count}"
    )

    # Log weight configuration for debugging
    if autoscaler_settings.enabled:
        logger.debug(
            f"Weight configuration - "
            f"Starship Launch: {autoscaler_settings.starship_launch_weight}, "
            f"Starship Event: {autoscaler_settings.starship_event_weight}, "
            f"SpaceX: {autoscaler_settings.spacex_weight}, "
            f"ULA: {autoscaler_settings.ula_weight}, "
            f"Rocket Lab: {autoscaler_settings.rocket_lab_weight}, "
            f"Other: {autoscaler_settings.other_weight}"
        )

    # If autoscaler is enabled and not using a custom count proceed.
    if autoscaler_settings.enabled and autoscaler_settings.custom_worker_count is None:
        logger.info("Autoscaler enabled - calculating expected worker count based on launches and events")

        # Get all launches and events that are +/- one hour and fifteen minutes
        # This is to ensure we have enough time to spin up resources before the T-Minus one hour notifs go out and
        # have enough workers online to handle the surge through the execution of the launch. One small scenario worth
        # considering is what happens if a launch has just scrubbed and had its date moved before the traffic dies down?
        logger.info(f"Max Workers: {autoscaler_settings.max_workers}")
        logger.info(f"Current Workers: {autoscaler_settings.current_workers}")

        # Calculate time thresholds
        now = dtime.datetime.now(tz=pytz.utc)
        threshold_plus_1_hour = now + dtime.timedelta(hours=1) + dtime.timedelta(minutes=10)
        threshold_minus_1_hour = now - dtime.timedelta(minutes=15)
        threshold_plus_24_hour = now + dtime.timedelta(hours=24) + dtime.timedelta(minutes=15)
        threshold_minus_24_hour = now + dtime.timedelta(hours=24) - dtime.timedelta(minutes=5)

        logger.debug(f"Current time: {now}")
        logger.debug(f"1-hour window: {threshold_minus_1_hour} to {threshold_plus_1_hour}")
        logger.debug(f"24-hour window: {threshold_minus_24_hour} to {threshold_plus_24_hour}")

        # Query launches and events
        launches_1 = Launch.objects.filter(net__range=[threshold_minus_1_hour, threshold_plus_1_hour])
        events = Events.objects.filter(date__range=[threshold_minus_1_hour, threshold_plus_1_hour])
        launches_24 = Launch.objects.filter(net__range=[threshold_minus_24_hour, threshold_plus_24_hour])
        launches = launches_1.union(launches_24)

        logger.info(f"Found {launches_1.count()} launches in 1-hour window")
        logger.info(f"Found {launches_24.count()} launches in 24-hour window")
        logger.info(f"Found {events.count()} events in 1-hour window")
        logger.info(f"Total unique launches to process: {launches.count()}")

        # Some providers have a heavier weight.
        expected_worker_count = 1
        logger.debug("Starting launch processing - initial worker count: 1")

        processed_launches = 0
        starship_launches = 0
        spacex_launches = 0
        ula_launches = 0
        rocket_lab_launches = 0
        other_launches = 0

        for launch in launches:
            processed_launches += 1
            launch_weight = 0
            launch_type = "other"

            if launch.program is not None and launch.program.count() > 1:
                program_names = [p.name for p in launch.program.all()]
                logger.debug(f"Launch {launch.id} ({launch.name}) has programs: {program_names}")

                has_starship = False
                program_weight = 0

                for program in launch.program.all():
                    if "Starship" in program.name:
                        program_weight += autoscaler_settings.starship_launch_weight
                        has_starship = True
                        logger.debug(f"Added Starship program weight: {autoscaler_settings.starship_launch_weight}")
                    else:
                        program_weight += autoscaler_settings.other_weight
                        logger.debug(f"Added other program weight: {autoscaler_settings.other_weight}")

                launch_weight = program_weight
                if has_starship:
                    launch_type = "Starship"
                    starship_launches += 1
                else:
                    launch_type = "program-other"
                    other_launches += 1
            elif "SpaceX" in launch.launch_service_provider.name:
                launch_weight = autoscaler_settings.spacex_weight
                launch_type = "SpaceX"
                spacex_launches += 1
            elif "United Launch Alliance" in launch.launch_service_provider.name:
                launch_weight = autoscaler_settings.ula_weight
                launch_type = "ULA"
                ula_launches += 1
            elif "Rocket Lab" in launch.launch_service_provider.name:
                launch_weight = autoscaler_settings.rocket_lab_weight
                launch_type = "Rocket Lab"
                rocket_lab_launches += 1
            else:
                launch_weight = autoscaler_settings.other_weight
                launch_type = "other"
                other_launches += 1

            expected_worker_count += launch_weight

            logger.debug(
                f"Launch {launch.id} ({launch.name}) - Provider: {launch.launch_service_provider.name}, "
                f"Type: {launch_type}, Weight: {launch_weight}, NET: {launch.net}"
            )

        logger.info(f"Launch processing complete - Processed: {processed_launches} launches")
        logger.info(
            f"Launch breakdown - Starship: {starship_launches}, SpaceX: {spacex_launches}, "
            f"ULA: {ula_launches}, Rocket Lab: {rocket_lab_launches}, Other: {other_launches}"
        )
        logger.debug(f"Worker count after launches: {expected_worker_count}")

        processed_events = 0
        starship_events = 0
        other_events = 0

        for event in events:
            processed_events += 1
            event_weight = autoscaler_settings.other_weight
            event_type = "other"

            expected_worker_count += event_weight

            if event.program is not None:
                program_names = [p.name for p in event.program.all()]
                logger.debug(f"Event {event.id} ({event.name}) has programs: {program_names}")

                for program in event.program.all():
                    if "Starship" in program.name:
                        additional_weight = autoscaler_settings.starship_event_weight
                        expected_worker_count += additional_weight
                        event_type = "Starship"
                        starship_events += 1
                        logger.debug(f"Event {event.id} - Added Starship weight: {additional_weight}")
                        break

            if event_type == "other":
                other_events += 1

            logger.debug(
                f"Event {event.id} ({event.name}) - Type: {event_type}, Base Weight: {event_weight}, Date: {event.date}"
            )

        logger.info(f"Event processing complete - Processed: {processed_events} events")
        logger.info(f"Event breakdown - Starship: {starship_events}, Other: {other_events}")
        logger.debug(f"Worker count after events: {expected_worker_count}")

        # Ensure we adhere to our max worker count.
        original_expected_count = expected_worker_count
        if expected_worker_count > autoscaler_settings.max_workers:
            expected_worker_count = autoscaler_settings.max_workers
            logger.warning(
                f"Expected worker count ({original_expected_count}) exceeds maximum "
                f"({autoscaler_settings.max_workers}), capping at maximum"
            )

        logger.info(f"Final calculated expected worker count: {expected_worker_count}")
        logger.debug(f"Expected workers calculated {expected_worker_count}")

        # Check to see if the expected worker count matches the current worker count and act.
        if expected_worker_count != autoscaler_settings.current_workers:
            logger.info(
                f"Scaling required - Expected: {expected_worker_count}, "
                f"Current: {autoscaler_settings.current_workers}, "
                f"Max: {autoscaler_settings.max_workers} - triggering update..."
            )

            # Update node pools
            logger.info("Updating DigitalOcean node pools")
            do.update_node_pools(expected_worker_count, autoscaler_settings.max_workers)

            # Also adjust KEDA ScaledObject minimum pod count based on expected traffic
            logger.info("Updating KEDA ScaledObject replicas")
            do.update_keda_min_replicas(expected_worker_count)

            logger.info("Autoscaler updates completed successfully")
        else:
            logger.info(
                f"No scaling required - current worker count ({autoscaler_settings.current_workers}) "
                f"matches expected count ({expected_worker_count})"
            )
            logger.debug("No changes required...")

    # If autoscaler is enabled and a customer worker count is set use that value instead of calculating.
    elif autoscaler_settings.enabled and autoscaler_settings.custom_worker_count is not None:
        expected_worker_count = autoscaler_settings.custom_worker_count
        logger.info(f"Autoscaler enabled with custom worker count: {expected_worker_count}")
        logger.debug(f"Expected workers custom set to  {expected_worker_count}")

        # Check to see if the expected worker count matches the current worker count and act.
        if expected_worker_count != autoscaler_settings.current_workers:
            logger.info(
                f"Custom scaling required - Expected: {expected_worker_count}, "
                f"Current: {autoscaler_settings.current_workers}, "
                f"Max: {autoscaler_settings.max_workers}"
            )

            # Update node pools
            logger.info("Updating DigitalOcean node pools (custom count)")
            do.update_node_pools(expected_worker_count, autoscaler_settings.max_workers)

            # Also adjust KEDA ScaledObject minimum pod count for custom worker count
            logger.info("Updating KEDA ScaledObject replicas (custom count)")
            do.update_keda_min_replicas(expected_worker_count)

            logger.info("Custom autoscaler updates completed successfully")
        else:
            logger.info(
                f"No custom scaling required - current worker count ({autoscaler_settings.current_workers}) "
                f"matches custom count ({expected_worker_count})"
            )
            logger.debug("No changes required...")

    else:
        logger.info("Autoscaler is disabled or no configuration set - no scaling actions will be taken")
        logger.debug(
            f"Autoscaler enabled: {autoscaler_settings.enabled}, "
            f"Custom worker count: {autoscaler_settings.custom_worker_count}"
        )
        logger.debug("Autoscaler is not enabled and no custom count set - doing nothing.")

    logger.info("Autoscaler check completed")
