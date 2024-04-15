import logging

from django.core import serializers
from django.utils.datetime_safe import datetime
from pytz import utc

from bot.models import DailyDigestRecord, LaunchNotificationRecord

logger = logging.getLogger(__name__)


def update_notification_record(launch):
    notification = LaunchNotificationRecord.objects.get(launch_id=launch.id)
    notification.last_net_stamp = launch.net
    notification.last_net_stamp_timestamp = datetime.now(tz=utc)
    logger.info(f"Updating Notification {launch.name} to timestamp {launch.net.strftime('%A %d %B %Y')}")
    notification.save()


def create_daily_digest_record(total, messages, launches):
    data = []

    for launch in launches:
        launch_json = serializers.serialize(
            "json",
            [
                launch,
            ],
        )
        data.append(launch_json)
    DailyDigestRecord.objects.create(timestamp=datetime.now(tz=utc), messages=messages, count=total, data=data)
