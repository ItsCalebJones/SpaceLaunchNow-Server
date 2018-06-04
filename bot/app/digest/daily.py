import pytz
from num2words import num2words

from bot.app.digest.sender import send_twitter_update
from bot.app.repository.launches_repository import *


# Get an instance of a logger
logger = logging.getLogger('bot.digest')


def check_launch_daily(DEBUG=True):
    confirmed_launches = []
    possible_launches = []
    repository = LaunchRepository()
    current_time = datetime.utcnow()
    for launch in repository.get_next_launches():
        update_notification_record(launch)
        if launch.netstamp > 0 and (datetime.utcfromtimestamp(int(launch.netstamp)) - current_time) \
                .total_seconds() < 172800:
            if launch.status == 1:
                confirmed_launches.append(launch)
            elif launch.status == 2:
                possible_launches.append(launch)
    build_daily_message(possible=possible_launches, confirmed=confirmed_launches, DEBUG=DEBUG)


def build_daily_message(possible, confirmed, DEBUG=True):
    logger.debug("Confirmed count - %s | Possible Count - %s" % (len(confirmed), len(possible)))
    header = "Daily Digest %s:" % datetime.strftime(datetime.now(), "%m/%d")
    messages = "MESSAGES SENT TO TWITTER: \n"
    if len(confirmed) == 0 and len(possible) == 0:
        logger.info("No launches - sending message. ")

        message = "%s There are currently no launches scheduled within the next 48 hours." % header

        messages = messages + message + "\n"
        send_twitter_update(message, DEBUG)

    if len(confirmed) == 1 and len(possible) == 0:
        launch = confirmed[0]

        current_time = datetime.utcnow()
        launch_time = datetime.utcfromtimestamp(int(launch.netstamp))
        logger.info("One launch - sending message. ")
        message = "%s %s launching from %s in %s hours. \n %s" % (
            header, launch.name, launch.location_set.all()[0].name,
            '{0:g}'.format(float(round(abs(launch_time - current_time).total_seconds() / 3600.0))),
            'https://spacelaunchnow.me/launch/%s' % launch.id)
        messages = messages + message + "\n"
        send_twitter_update(message, DEBUG)

    if len(confirmed) == 0 and len(possible) == 1:
        launch = possible[0]

        logger.info("One launch - sending message. ")
        date = datetime.utcfromtimestamp(launch.netstamp).replace(tzinfo=pytz.UTC)
        message = "%s %s might be launching from %s on %s." % (
            header, launch.name, launch.location_set.all()[0].name,
            date.strftime("%A at %H:%S %Z"))
        messages = messages + message + "\n"
        send_twitter_update(message, DEBUG)

    if len(confirmed) == 1 and len(possible) == 1:
        possible_launch = possible[0]
        confirmed_launch = confirmed[0]

        logger.info("One launch possible - sending message. ")
        date = datetime.utcfromtimestamp(possible_launch.netstamp).replace(tzinfo=pytz.UTC)
        message = "%s %s might be launching from %s on %s." % (header, possible_launch.name,
                                                               possible_launch.location_set.all()[0].name,
                                                               date.strftime("%A at %H:%S %Z"))
        messages = messages + message + "\n"
        response_id = send_twitter_update(message, DEBUG)

        current_time = datetime.utcnow()
        launch_time = datetime.utcfromtimestamp(int(confirmed_launch.netstamp))
        logger.info("One launch confirmed - sending message. ")
        message = "%s %s launching from %s in %s hours. \n %s" % (
            header, confirmed_launch.name, confirmed_launch.location_set.all()[0].name,
            '{0:g}'.format(float(round(abs(launch_time - current_time).total_seconds() / 3600.0))),
            'https://spacelaunchnow.me/launch/%s' % launch.id)
        messages = messages + message + "\n"
        send_twitter_update(message, DEBUG, response_id)

    if len(confirmed) > 1 and len(possible) == 0:
        logger.info("More then one launch - sending summary first. ")
        message = "%s There are %i confirmed launches within the next 48 hours...(1/%i)" % (header,
                                                                                            len(confirmed),
                                                                                            len(confirmed) + 1)

        messages = messages + message + "\n"
        response_id = send_twitter_update(message, DEBUG)
        for index, launch in enumerate(confirmed, start=1):
            current_time = datetime.utcnow()

            launch_time = datetime.utcfromtimestamp(int(launch.netstamp))
            message = "%s launching from %s in %s hours. (%i/%i) \n %s" % (
                launch.name,
                launch.location_set.all()[0].name,
                '{0:g}'.format(float(round(abs(launch_time - current_time).total_seconds() / 3600.0))),
                index + 1, len(confirmed) + 1,
                'https://spacelaunchnow.me/launch/%s' % launch.id)
            messages = messages + message + "\n"
            response_id = send_twitter_update(message, DEBUG, response_id)

    if len(confirmed) == 0 and len(possible) > 1:
        logger.info("More then one launch - sending summary first. ")
        message = "%s There are %s possible launches within the next 48 hours...(1/%i)" % (header,
                                                                                           num2words(len(possible)),
                                                                                           len(possible) + 1)
        messages = messages + message + "\n"
        response_id = send_twitter_update(message, DEBUG)
        for index, launch in enumerate(possible, start=1):
            date = datetime.utcfromtimestamp(launch.netstamp).replace(tzinfo=pytz.UTC)
            message = "%s might be launching from %s on %s. (%i/%i)" % (launch.name,
                                                                        launch.location_set.all()[0].name,
                                                                        date.strftime("%A at %H:%S %Z"),
                                                                        index + 1, len(possible) + 1)
            messages = messages + message + "\n"
            response_id = send_twitter_update(message, DEBUG, response_id)

    if len(confirmed) > 1 and len(possible) > 1:
        total = confirmed + possible
        logger.info("More then one launch - sending summary first. ")
        message = "%s There are %i possible and %i confirmed launches within the next 48 hours." % (header,
                                                                                                    num2words(len(
                                                                                                        possible)),
                                                                                                    num2words(len(
                                                                                                        confirmed)))
        messages = messages + message + "\n"
        response_id = send_twitter_update(message, DEBUG)

        # Possible launches
        for index, launch in enumerate(possible, start=1):
            message = "%s might be launching from %s on %s. (%i/%i)" % (launch.name,
                                                                        launch.location_set.all()[0].name,
                                                                        datetime.fromtimestamp(launch
                                                                                               .launch.netstamp)
                                                                        .strftime("%A at %H:%S %Z"),
                                                                        index, len(total))
            messages = messages + message + "\n"
            response_id = send_twitter_update(message, DEBUG, response_id)

        # Confirmed launches
        for index, launch in enumerate(confirmed, start=1):
            current_time = datetime.utcnow()

            launch_time = datetime.utcfromtimestamp(int(launch.netstamp))
            message = "%s launching from %s in %s hours. (%i/%i) \n %s" % (
                launch.name,
                launch.location_set.all()[0].name,
                '{0:g}'.format(float(round(abs(launch_time - current_time).total_seconds() / 3600.0))),
                possible + index, len(total), 'https://spacelaunchnow.me/launch/%s' % launch.id)
            messages = messages + message + "\n"
            send_twitter_update(message, DEBUG, response_id)

    create_daily_digest_record(len(confirmed) + len(possible), messages, confirmed + possible)
