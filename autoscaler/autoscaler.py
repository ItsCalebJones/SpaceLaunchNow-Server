import logging

from api.models import Launch, Events

from autoscaler.jenkins import *
from autoscaler.digitalocean_helper import *
import datetime as dtime
import pytz

logger = logging.getLogger('autoscaler')


def check_autoscaler():
    do = DigitalOceanHelper()
    jenkins = DevOpsJenkins()
    max_worker_count = 5
    worker_count = do.get_worker_node_count()
    logger.info("Max Worker Count: %s" % max_worker_count)
    logger.info("Current Count: %s" % worker_count)
    threshold_plus_1_hour = dtime.datetime.now(tz=pytz.utc) + dtime.timedelta(hours=1) + dtime.timedelta(minutes=15)
    threshold_minus_1_hour = dtime.datetime.now(tz=pytz.utc) - dtime.timedelta(hours=1) - dtime.timedelta(minutes=15)

    launches = Launch.objects.filter(net__lte=threshold_plus_1_hour,
                                     net__gte=threshold_minus_1_hour,
                                     notifications_enabled=True)

    events = Events.objects.filter(date__lte=threshold_plus_1_hour,
                                   date__gte=threshold_minus_1_hour,
                                   notifications_enabled=True)

    expected_worker_count = 0
    for launch in launches:
        if "SpaceX" in launch.launch_service_provider.name:
            expected_worker_count += 3
        elif "United Launch Alliance" in launch.launch_service_provider.name:
            expected_worker_count += 2
        elif "Rocket Lab" in launch.launch_service_provider.name:
            expected_worker_count += 2
        else:
            expected_worker_count += 1

    for event in events:
        if event.program is not None:
            for program in event.program.all():
                if "Starship" in program.name:
                    expected_worker_count += 2
        else:
            expected_worker_count += 1

    if expected_worker_count > max_worker_count:
        expected_worker_count = max_worker_count

    if expected_worker_count != worker_count:
        logger.info(f"Expected {expected_worker_count} vs actual  {worker_count} - triggering Terraform...")
        jenkins.scale_worker_count(expected_worker_count)
    else:
        logger.info(f"No changes required...")
