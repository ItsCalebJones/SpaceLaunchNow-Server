import pytz
from num2words import num2words

from api.models import Launch
from bot.app.digest.sender import send_twitter_update
from bot.app.repository.launches_repository import *


# Get an instance of a logger
from bot.utils.util import custom_strftime

logger = logging.getLogger('digest')


def check_launch_daily(DEBUG=True):
    confirmed_launches = []
    possible_launches = []
    repository = LaunchRepository()
    current_time = datetime.now(tz=pytz.utc)
    for launch in repository.get_next_launches():
        update_notification_record(launch)
        if launch.net and (launch.net - current_time).total_seconds() < 172800:
            if launch.status.id == 1:
                confirmed_launches.append(launch)
            elif launch.status.id == 2:
                possible_launches.append(launch)
    build_daily_message(possible=possible_launches, confirmed=confirmed_launches, DEBUG=DEBUG)


def build_daily_message(possible, confirmed, DEBUG=True):
    logger.debug("Confirmed count - %s | Possible Count - %s" % (len(confirmed), len(possible)))
    current_time = datetime.now(tz=pytz.utc)
    header = "Daily Digest %s:" % current_time.strftime("%m/%d")
    messages = "MESSAGES SENT TO TWITTER: \n"
    if len(confirmed) == 0 and len(possible) == 0:
        logger.info("No launches - sending message. ")
        launch = Launch.objects.filter(net__gte=current_time).order_by('net').first()

        message = "%s There are currently no launches scheduled within the next 48 hours. Next up is %s on %s" % (header, launch.name, custom_strftime("%B {S} at %I:%M %p %Z", launch.net))

        messages = messages + message + "\n"
        send_twitter_update(message, DEBUG)

    if len(confirmed) == 1 and len(possible) == 0:
        launch = confirmed[0]
        launch_time = launch.net
        logger.info("One launch - sending message. ")
        message = "%s %s launching from %s in %s hours. \n %s" % (
            header, launch.name, launch.pad.location.name,
            '{0:g}'.format(float(round(abs(launch_time - current_time).total_seconds() / 3600.0))),
            'https://spacelaunchnow.me/launch/%s' % launch.slug)
        messages = messages + message + "\n"
        send_twitter_update(message, DEBUG)

    if len(confirmed) == 0 and len(possible) == 1:
        launch = possible[0]

        logger.info("One launch - sending message. ")
        date = launch.net
        message = "%s %s might be launching from %s on %s." % (
            header, launch.name, launch.pad.location.name,
            date.strftime("%A at %H:%S %Z"))
        messages = messages + message + "\n"
        send_twitter_update(message, DEBUG)

    if len(confirmed) == 1 and len(possible) == 1:
        possible_launch = possible[0]
        confirmed_launch = confirmed[0]

        logger.info("One launch possible - sending message. ")
        date = possible_launch.net
        message = "%s %s might be launching from %s on %s." % (header, possible_launch.name,
                                                               possible_launch.pad.location.name,
                                                               date.strftime("%A at %H:%S %Z"))
        messages = messages + message + "\n"
        response_id = send_twitter_update(message, DEBUG)

        launch_time = confirmed_launch.net
        logger.info("One launch confirmed - sending message. ")
        message = "%s %s launching from %s in %s hours. \n %s" % (
            header, confirmed_launch.name, confirmed_launch.pad.location.name,
            '{0:g}'.format(float(round(abs(launch_time - current_time).total_seconds() / 3600.0))),
            'https://spacelaunchnow.me/launch/%s' % launch.slug)
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

            launch_time = launch.net
            message = "%s launching from %s in %s hours. (%i/%i) \n %s" % (
                launch.name,
                launch.pad.location.name,
                '{0:g}'.format(float(round(abs(launch_time - current_time).total_seconds() / 3600.0))),
                index + 1, len(confirmed) + 1,
                'https://spacelaunchnow.me/launch/%s' % launch.slug)
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
            date = launch.net
            message = "%s might be launching from %s on %s. (%i/%i)" % (launch.name,
                                                                        launch.pad.location.name,
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
                                                                        launch.pad.location.name,
                                                                        launch.net.strftime("%A at %H:%S %Z"),
                                                                        index, len(total))
            messages = messages + message + "\n"
            response_id = send_twitter_update(message, DEBUG, response_id)

        # Confirmed launches
        for index, launch in enumerate(confirmed, start=1):

            launch_time = launch.net
            message = "%s launching from %s in %s hours. (%i/%i) \n %s" % (
                launch.name,
                launch.pad.location.name,
                '{0:g}'.format(float(round(abs(launch_time - current_time).total_seconds() / 3600.0))),
                possible + index, len(total), 'https://spacelaunchnow.me/launch/%s' % launch.slug)
            messages = messages + message + "\n"
            send_twitter_update(message, DEBUG, response_id)

    create_daily_digest_record(len(confirmed) + len(possible), messages, confirmed + possible)
