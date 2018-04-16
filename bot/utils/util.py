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


def get_fcm_topics_and_onesignal_segments(launch, debug=False):
    location_agency_id = 0
    rocket_agency_id = 0
    location_id = 0
    segments = ['ALL-Filter']
    if not debug:
        topics = "'production' in topics"
    else:
        topics = "'debug' in topics"

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
        topics = topics + " && ('all' in topics || 'nasa' in topics)"
        segments.append('Nasa')
        return {'segments': segments, 'topics': topics}
    if lsp_id == 115 or location_agency_id == 115 or rocket_agency_id == 115:
        topics = topics + " && ('all' in topics || 'arianespace' in topics)"
        segments.append('Arianespace')
        return {'segments': segments, 'topics': topics}
    if lsp_id == 121 or location_agency_id == 121 or rocket_agency_id == 121:
        topics = topics + " && ('all' in topics || 'spacex' in topics)"
        segments.append('SpaceX')
        return {'segments': segments, 'topics': topics}
    if lsp_id == 124 or location_agency_id == 124 or rocket_agency_id == 124:
        topics = topics + " && ('all' in topics || 'ula' in topics)"
        segments.append('ULA')
        return {'segments': segments, 'topics': topics}
    if lsp_id == 111 or location_agency_id == 111 or rocket_agency_id == 111 or location_agency_id == 163 \
            or rocket_agency_id == 163 or location_agency_id == 63 or rocket_agency_id == 63:
        topics = topics + " && ('all' in topics || 'roscosmos' in topics)"
        segments.append('Roscosmos')
        return {'segments': segments, 'topics': topics}
    if lsp_id == 88 or location_agency_id == 88 or rocket_agency_id == 88:
        topics = topics + " && ('all' in topics || 'casc' in topics)"
        segments.append('CASC')
        return {'segments': segments, 'topics': topics}
    if location_id == 17:
        topics = topics + " && ('all' in topics || 'ksc' in topics)"
        segments.append('KSC')
        return {'segments': segments, 'topics': topics}
    if location_id == 17:
        topics = topics + " && ('all' in topics || 'cape' in topics)"
        segments.append('Cape')
        return {'segments': segments, 'topics': topics}
    if location_id == 11:
        topics = topics + " && ('all' in topics || 'plex' in topics)"
        segments.append('Ples')
        return {'segments': segments, 'topics': topics}
    if location_id == 11:
        topics = topics + " && ('all' in topics || 'van' in topics)"
        segments.append('Van')
        return {'segments': segments, 'topics': topics}
    topics = topics + " && 'all' in topics"
    return {'segments': segments, 'topics': topics}


def get_onesignal_segments(launch):
    location_agency_id = 0
    rocket_agency_id = 0
    location_id = 0
    segments = ['ALL-Filter']
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
        segments.append('NASA')
    if lsp_id == 115 or location_agency_id == 115 or rocket_agency_id == 115:
        segments.append('Arianespace')
    if lsp_id == 121 or location_agency_id == 121 or rocket_agency_id == 121:
        segments.append('SpaceX')
    if lsp_id == 124 or location_agency_id == 124 or rocket_agency_id == 124:
        segments.append('ULA')
    if lsp_id == 111 or location_agency_id == 111 or rocket_agency_id == 111 or location_agency_id == 163 \
            or rocket_agency_id == 163 or location_agency_id == 63 or rocket_agency_id == 63:
        segments.append('Roscosmos')
    if lsp_id == 88 or location_agency_id == 88 or rocket_agency_id == 88:
        segments.append('CASC')
    if location_id == 17:
        segments.append('KSC')
    if location_id == 17:
        segments.append('Cape')
    if location_id == 11:
        segments.append('Ples')
    if location_id == 11:
        segments.append('Van')
    return segments
