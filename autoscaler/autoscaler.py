import logging

from api.models import Launch, Events

from autoscaler.jenkins import *
from autoscaler.digitalocean_helper import *
import datetime as dtime
import pytz

from autoscaler.models import AutoscalerSettings

logger = logging.getLogger('autoscaler')


def check_autoscaler():
    # First initialize helper classes.
    do = DigitalOceanHelper()
    jenkins = DevOpsJenkins()

    # Get Autoscaler settings and make sure the latest worker node count is correct
    autoscaler_settings = AutoscalerSettings.load()
    autoscaler_settings.current_workers = do.get_worker_node_count()
    autoscaler_settings.save()

    # If autoscaler is enabled and not using a custom count proceed.
    if autoscaler_settings.enabled and autoscaler_settings.custom_worker_count is None:

        # Get all launches and events that are +/- one hour and fifteen minutes
        # This is to ensure we have enough time to spin up resources before the T-Minus one hour notifs go out and
        # have enough workers online to handle the surge through the execution of the launch. One small scenario worth
        # considering is what happens if a launch has just scrubbed and had its date moved before the traffic dies down?
        logger.info("Max Workers: %s" % autoscaler_settings.max_workers)
        logger.info("Current Workers: %s" % autoscaler_settings.current_workers)
        threshold_plus_1_hour = dtime.datetime.now(tz=pytz.utc) + dtime.timedelta(hours=1) + dtime.timedelta(minutes=30)
        threshold_minus_1_hour = dtime.datetime.now(tz=pytz.utc) - dtime.timedelta(hours=1) - dtime.timedelta(minutes=30)

        launches = Launch.objects.filter(net__lte=threshold_plus_1_hour,
                                         net__gte=threshold_minus_1_hour,
                                         notifications_enabled=True)

        events = Events.objects.filter(date__lte=threshold_plus_1_hour,
                                       date__gte=threshold_minus_1_hour,
                                       notifications_enabled=True)

        # Some providers have a heavier weight.
        expected_worker_count = 0
        for launch in launches:
            if launch.program is not None and launch.program.count() > 1:
                for program in launch.program.all():
                    if "Starship" in program.name:
                        expected_worker_count += autoscaler_settings.starship_launch_weight
            elif "SpaceX" in launch.launch_service_provider.name:
                expected_worker_count += autoscaler_settings.spacex_weight
            elif "United Launch Alliance" in launch.launch_service_provider.name:
                expected_worker_count += autoscaler_settings.ula_weight
            elif "Rocket Lab" in launch.launch_service_provider.name:
                expected_worker_count += autoscaler_settings.rocket_lab_weight
            else:
                expected_worker_count += autoscaler_settings.other_weight

        for event in events:
            if event.program is not None:
                for program in event.program.all():
                    if "Starship" in program.name:
                        expected_worker_count += autoscaler_settings.starship_event_weight
            else:
                expected_worker_count += autoscaler_settings.other_weight

        # Ensure we adhere to our max worker count.
        if expected_worker_count > autoscaler_settings.max_workers:
            expected_worker_count = autoscaler_settings.max_workers
        logger.debug(f"Expected workers calculated {expected_worker_count}")
        # Check to see if the expected worker count matches the current worker count and act.
        if expected_worker_count != autoscaler_settings.current_workers:
            logger.info(f"Expected {expected_worker_count} vs actual {autoscaler_settings.current_workers} - triggering Terraform...")
            jenkins.scale_worker_count(expected_worker_count)
        else:
            logger.debug(f"No changes required...")

    # If autoscaler is enabled and a customer worker count is set use that value instead of calculating.
    elif autoscaler_settings.enabled and autoscaler_settings.custom_worker_count is not None:
        expected_worker_count = autoscaler_settings.custom_worker_count
        logger.debug(f"Expected workers custom set to  {expected_worker_count}")
        # Check to see if the expected worker count matches the current worker count and act.
        if expected_worker_count != autoscaler_settings.current_workers:
            logger.info(f"Custom - Expected {expected_worker_count} vs actual {autoscaler_settings.current_workers} - triggering Terraform...")
            jenkins.scale_worker_count(expected_worker_count)
        else:
            logger.debug(f"No changes required...")

    else:
        logger.debug(f"Autoscaler is not enabled and no custom count set - doing nothing.")
