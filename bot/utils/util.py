import datetime
# import the logging library
import logging

# Get an instance of a logger
logger = logging.getLogger('bot.utils.util')


def log(tag, message):
    logger.debug(message)
    log_message = ('%s - %s: %s' % ('{:%H:%M:%S %m-%d-%Y}'.format(datetime.datetime.now()), tag, message))
    print log_message


def log_error(tag, message):
    logger.error(message)
    log_message = ('ERROR: %s - %s: %s' % ('{:%H:%M:%S %m-%d-%Y}'.format(datetime.datetime.now()), tag, message))
    print log_message


def seconds_to_time(seconds):
    seconds_in_day = 86400
    seconds_in_hour = 3600
    seconds_in_minute = 60

    days = seconds // seconds_in_day
    seconds -= days * seconds_in_day

    hours = seconds // seconds_in_hour
    seconds -= hours * seconds_in_hour

    minutes = seconds // seconds_in_minute
    seconds -= minutes * seconds_in_minute
    if days > 0:
        return "{0:.0f} days, {1:.0f} hours".format(days, hours)
    elif hours == 23:
        return "24 hours"
    elif hours > 0:
        return "{0:.0f} hours, {1:.0f} minutes".format(hours, minutes)
    elif minutes > 0:
        return "{0:.0f} minutes".format(minutes)
