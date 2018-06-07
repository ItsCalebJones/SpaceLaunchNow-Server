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
        if minutes < 10:
            return "less then ten minutes"
        if minutes < 60:
            return "less then one hour"
        return "{0:.0f} minutes".format(minutes)


def build_topics(topic_header, topics_set):
    topics = topic_header + " && "
    first = True
    for topic in topics_set:
        if first:
            topics = topics + "('" + topic + "' in topics"
            first = False
        else:
            topics = topics + " || '" + topic + "' in topics"
    topics = topics + ")"
    return topics


def get_fcm_topics_and_onesignal_segments(launch, debug=False, flutter=False, notification_type=None):
    location_agency_id = 0
    rocket_agency_id = 0
    location_id = 0
    segments = ['ALL-Filter']
    topics_set = ['all']
    if flutter:
        if not debug:
            topic_header = "'flutter_production' in topics && %s in topics" % notification_type
        else:
            topic_header = "'flutter_debug' in topics && %s in topics" % notification_type
    else:
        if not debug:
            topic_header = "'production' in topics"
        else:
            topic_header = "'debug' in topics"

    if launch.location_set.first() is not None:
        location_id = launch.location_set.first().id
        if launch.location_set.first().pad_set.first() is not None:
            pad_id = launch.location_set.first().pad_set.first().id
            if launch.location_set.first().pad_set.first().agency_set.first() is not None:
                location_agency_id = launch.location_set.first().pad_set.first().agency_set.first().id
    if launch.rocket_set.first() is not None:
        rocket_id = launch.rocket_set.first().id
        if launch.rocket_set.first().agency_set.first() is not None:
            rocket_agency_id = launch.rocket_set.first().agency_set.first().id
    lsp_id = launch.lsp_set.first().id

    if lsp_id == 44 or location_agency_id == 44 or rocket_agency_id == 44:
        topics_set.append('nasa')
        segments.append('Nasa')
    if lsp_id == 115 or location_agency_id == 115 or rocket_agency_id == 115:
        topics_set.append('arianespace')
        segments.append('Arianespace')
    if lsp_id == 121 or location_agency_id == 121 or rocket_agency_id == 121:
        topics_set.append('spacex')
        segments.append('SpaceX')
    if lsp_id == 124 or location_agency_id == 124 or rocket_agency_id == 124:
        topics_set.append('ula')
        segments.append('ULA')
    if lsp_id == 111 or location_agency_id == 111 or rocket_agency_id == 111 or location_agency_id == 163 \
            or rocket_agency_id == 163 or location_agency_id == 63 or rocket_agency_id == 63:
        topics_set.append('roscosmos')
        segments.append('Roscosmos')
    if lsp_id == 88 or location_agency_id == 88 or rocket_agency_id == 88:
        topics_set.append('casc')
        segments.append('CASC')
    if location_id == 16:
        topics_set.append('ksc')
        segments.append('KSC')
    if location_id == 16:
        topics_set.append('cape')
        segments.append('Cape')
    if location_id == 11:
        topics_set.append('ples')
        segments.append('Ples')
    if location_id == 18:
        topics_set.append('van')
        segments.append('Van')
    topics = build_topics(topic_header, topics_set)
    return {'segments': segments, 'topics': topics}
