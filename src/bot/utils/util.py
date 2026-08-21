import datetime
import logging

from api.models import Astronaut, Events, Launch
from PIL import Image, ImageFilter

logger = logging.getLogger(__name__)


def log(tag, message):
    logger.debug(message)
    log_message = f"{datetime.datetime.now():%H:%M:%S %m-%d-%Y} - {tag}: {message}"
    print(log_message)


def log_error(tag, message):
    logger.error(message)
    log_message = f"ERROR: {datetime.datetime.now():%H:%M:%S %m-%d-%Y} - {tag}: {message}"
    print(log_message)


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
        return f"{days:.0f} days, {hours:.0f} hours"
    elif hours == 23:
        return "24 hours"
    elif hours > 0:
        return f"{hours:.0f} hours, {minutes:.0f} minutes"
    elif minutes > 0:
        if minutes < 10:
            return "less than ten minutes"
        if minutes < 60:
            return "less than one hour"
        return f"{minutes:.0f} minutes"


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


def get_fcm_strict_topics_v3(launch, debug=False, flutter=False, notification_type=None):
    location_id = 0
    lsp_topic = None
    location_topic = None
    other_topic = None
    topics = None

    if flutter:
        if not debug:
            topic_header = f"'flutter_production_v3' in topics && '{notification_type}' in topics && 'strict' in topics"
        else:
            topic_header = f"'flutter_debug_v3' in topics && '{notification_type}' in topics && 'strict' in topics"
    else:
        if not debug:
            topic_header = f"'prod_v3' in topics && '{notification_type}' in topics && 'strict' in topics"
        else:
            topic_header = f"'debug_v3' in topics && '{notification_type}' in topics && 'strict' in topics"

    if launch.pad.location is not None:
        location_id = launch.pad.location.id
    lsp_id = launch.launch_service_provider.id

    if lsp_id == 44:
        lsp_topic = "nasa"
    elif lsp_id == 115:
        lsp_topic = "arianespace"
    elif lsp_id == 121:
        lsp_topic = "spacex"
    elif lsp_id == 124:
        lsp_topic = "ula"
    elif lsp_id == 111 or lsp_id == 63 or lsp_id == 163:
        lsp_topic = "roscosmos"
    elif lsp_id == 141:
        lsp_topic = "blueOrigin"
    elif lsp_id == 147:
        lsp_topic = "rocketLab"
    elif lsp_id == 257:
        lsp_topic = "northrop"

    # Locations
    if location_id == 27 or location_id == 12:
        location_topic = "ksc"
    elif location_id == 15 or location_id == 5 or location_id == 6 or location_id == 18:
        location_topic = "russia"
    elif location_id == 11:
        location_topic = "van"
    elif location_id == 21:
        location_topic = "wallops"
    elif location_id == 10:
        location_topic = "newZealand"
    elif location_id == 13:
        location_topic = "frenchGuiana"
    elif location_id == 143 or location_id == 9999 or location_id == 29:
        location_topic = "texas"

    if location_id == 20 or location_id == 144 or location_id == 22 or location_id == 3:
        other_topic = "other"
    elif location_id == 25:
        other_topic = "kodiak"
    elif location_id == 24 or location_id == 26 or location_id == 32:
        other_topic = "japan"
    elif location_id == 14 or lsp_id == 31:
        other_topic = "isro"
    elif location_id == 17 or location_id == 19 or location_id == 8 or location_id == 16 or location_id == 148:
        other_topic = "china"

    if lsp_topic and location_topic:
        topics = topic_header + f" && ('{lsp_topic}' in topics && '{location_topic}' in topics)"
    elif other_topic:
        topics = topic_header + f" && '{other_topic}' in topics"
    else:
        return None

    logger.info(topics)
    return topics


def get_fcm_not_strict_topics_v3(launch, debug=False, flutter=False, notification_type=None):
    location_id = 0
    lsp_topic = None
    location_topic = None

    if flutter:
        if not debug:
            topic_header = (
                f"'flutter_production_v3' in topics && '{notification_type}' in topics && 'not_strict' in topics"
            )
        else:
            topic_header = f"'flutter_debug_v3' in topics && '{notification_type}' in topics && 'not_strict' in topics"
    else:
        if not debug:
            topic_header = f"'prod_v3' in topics && '{notification_type}' in topics && 'not_strict' in topics"
        else:
            topic_header = f"'debug_v3' in topics && '{notification_type}' in topics && 'not_strict' in topics"

    if launch.pad.location is not None:
        location_id = launch.pad.location.id
    lsp_id = launch.launch_service_provider.id

    if lsp_id == 44:
        lsp_topic = "nasa"
    elif lsp_id == 115:
        lsp_topic = "arianespace"
    elif lsp_id == 121:
        lsp_topic = "spacex"
    elif lsp_id == 124:
        lsp_topic = "ula"
    elif lsp_id == 111 or lsp_id == 63 or lsp_id == 163:
        lsp_topic = "roscosmos"
    elif lsp_id == 141:
        lsp_topic = "blueOrigin"
    elif lsp_id == 147:
        lsp_topic = "rocketLab"
    elif lsp_id == 257:
        lsp_topic = "northrop"

    if location_id == 27 or location_id == 12:
        location_topic = "ksc"
    elif location_id == 15 or location_id == 5 or location_id == 6 or location_id == 18:
        location_topic = "russia"
    elif location_id == 11:
        location_topic = "van"
    elif location_id == 21:
        location_topic = "wallops"
    elif location_id == 10:
        location_topic = "newZealand"
    elif location_id == 13:
        location_topic = "frenchGuiana"
    elif location_id == 143 or location_id == 9999 or location_id == 29:
        location_topic = "texas"
    elif location_id == 20 or location_id == 144 or location_id == 22 or location_id == 3:
        location_topic = "other"
    elif location_id == 25:
        location_topic = "kodiak"
    elif location_id == 24 or location_id == 26 or location_id == 32:
        location_topic = "japan"
    elif location_id == 14 or lsp_id == 31:
        location_topic = "isro"
    elif location_id == 17 or location_id == 19 or location_id == 8 or location_id == 16 or location_id == 148:
        location_topic = "china"

    if lsp_topic and location_topic:
        topics = topic_header + f" && ('{lsp_topic}' in topics || '{location_topic}' in topics)"
    elif lsp_topic:
        topics = topic_header + f" && '{lsp_topic}' in topics"
    elif location_topic:
        topics = topic_header + f" && '{location_topic}' in topics"
    else:
        return None

    logger.info(topics)
    return topics


def get_fcm_all_topics_v3(debug=False, flutter=False, notification_type=None):
    if flutter:
        if not debug:
            topic_header = f"'flutter_production_v3' in topics && '{notification_type}' in topics"
        else:
            topic_header = f"'flutter_debug_v3' in topics && '{notification_type}' in topics"
    else:
        if not debug:
            topic_header = f"'prod_v3' in topics && '{notification_type}' in topics"
        else:
            topic_header = f"'debug_v3' in topics && '{notification_type}' in topics"
    topics = topic_header + " && 'all' in topics"
    logger.info(topics)
    return topics


def get_flutter_topics_v3(launch, debug=False, flutter=False, notification_type=None):
    location_id = 0
    topics_set = ["all"]
    if flutter:
        if not debug:
            topic_header = f"'flutter_production_v3' in topics && '{notification_type}' in topics"
        else:
            topic_header = f"'flutter_debug_v3' in topics && '{notification_type}' in topics"
    else:
        if not debug:
            topic_header = f"'prod_v2' in topics && '{notification_type}' in topics"
        else:
            topic_header = f"'debug_v2' in topics && '{notification_type}' in topics"

    if launch.pad.location is not None:
        location_id = launch.pad.location.id
    lsp_id = launch.launch_service_provider.id

    # LSPs
    if lsp_id == 44:
        topics_set.append("nasa")
    if lsp_id == 115:
        topics_set.append("arianespace")
    if lsp_id == 121:
        topics_set.append("spacex")
    if lsp_id == 124:
        topics_set.append("ula")
    if lsp_id == 111 or lsp_id == 63 or lsp_id == 163:
        topics_set.append("roscosmos")
    if lsp_id == 141:
        topics_set.append("blueOrigin")
    if lsp_id == 147:
        topics_set.append("rocketLab")
    if lsp_id == 257:
        topics_set.append("northrop")

    # Locations
    if location_id == 17 or location_id == 19 or location_id == 8 or location_id == 16:
        topics_set.append("china")
    if location_id == 27 or location_id == 12:
        topics_set.append("ksc")
    if location_id == 15 or location_id == 5 or location_id == 6 or location_id == 18:
        topics_set.append("russia")
    if location_id == 11:
        topics_set.append("van")
    if location_id == 14 or lsp_id == 31:
        topics_set.append("isro")
    if location_id == 21:
        topics_set.append("wallops")
    if location_id == 10:
        topics_set.append("newZealand")
    if location_id == 24 or location_id == 26:
        topics_set.append("japan")
    if location_id == 13:
        topics_set.append("frenchGuiana")

    topics = build_topics(topic_header, topics_set)
    return topics


def suffix(d):
    return "th" if 11 <= d <= 13 else {1: "st", 2: "nd", 3: "rd"}.get(d % 10, "th")


def custom_strftime(format, t):
    return t.strftime(format).replace("{S}", str(t.day) + suffix(t.day))


def drop_shadow(image, offset=(5, 5), background=0xFFFFFF, shadow=0x444444, border=8, iterations=5):
    """
    Add a gaussian blur drop shadow to an image.

    image       - The image to overlay on top of the shadow.
    offset      - Offset of the shadow from the image as an (x,y) tuple.  Can be
                  positive or negative.
    background  - Background colour behind the image.
    shadow      - Shadow colour (darkness).
    border      - Width of the border around the image.  This must be wide
                  enough to account for the blurring of the shadow.
    iterations  - Number of times to apply the filter.  More iterations
                  produce a more blurred shadow, but increase processing time.
    """

    # Create the backdrop image -- a box in the background colour with a
    # shadow on it.
    totalWidth = image.size[0] + abs(offset[0]) + 2 * border
    totalHeight = image.size[1] + abs(offset[1]) + 2 * border
    back = Image.new(image.mode, (totalWidth, totalHeight), background)

    # Place the shadow, taking into account the offset from the image
    shadowLeft = border + max(offset[0], 0)
    shadowTop = border + max(offset[1], 0)
    back.paste(shadow, [shadowLeft, shadowTop, shadowLeft + image.size[0], shadowTop + image.size[1]])

    # Apply the filter to blur the edges of the shadow.  Since a small kernel
    # is used, the filter must be applied repeatedly to get a decent blur.
    n = 0
    while n < iterations:
        back = back.filter(ImageFilter.BLUR)
        n += 1

    # Paste the input image onto the shadow backdrop
    imageLeft = border - min(offset[0], 0)
    imageTop = border - min(offset[1], 0)
    back.paste(image, (imageLeft, imageTop))

    return back


def get_SLN_url(path: str = None, object: Launch | Events | Astronaut = None):
    return f"https://spacelaunchnow.app/{path}/{object.get_absolute_url()}"


def get_agency_topic(launch: Launch) -> int:
    """Get the agency ID (LSP ID) for a launch."""
    return launch.launch_service_provider.id


def get_location_topic(launch: Launch) -> int:
    """Get the location ID for a launch."""
    if launch.pad.location is not None:
        return launch.pad.location.id
    return 0


def get_fcm_v4_topic(debug: bool = False) -> str:
    """Get the simplified v4 topic condition."""
    if debug:
        return "'k_debug_v4' in topics"
    return "'k_prod_v4' in topics"


def get_fcm_v5_android_topic(debug: bool = False) -> str:
    """Get FCM topic condition for v5 Android notifications.

    Returns a topic condition string for data-only Android notifications.
    Filtering is handled client-side, so only the base topic is included.

    Args:
        debug: Whether to use debug or production topic
        notification_type: The notification type (e.g., 'tenMinutes', 'oneHour')

    Returns:
        FCM topic condition string
    """
    topic_base = "debug_v5_android" if debug else "prod_v5_android"
    topics = f"'{topic_base}' in topics"
    logger.info(topics)
    return topics


def get_fcm_v5_ios_topic(debug: bool = False) -> str:
    """Get FCM topic condition for v5 iOS notifications.

    Returns a topic condition string for iOS notifications with mutable-content
    for Notification Service Extension processing. Filtering is handled client-side.

    Args:
        debug: Whether to use debug or production topic
        notification_type: The notification type (e.g., 'tenMinutes', 'oneHour')

    Returns:
        FCM topic condition string
    """
    topic_base = "debug_v5_ios" if debug else "prod_v5_ios"
    topics = f"'{topic_base}' in topics"
    logger.info(topics)
    return topics


# --------------------------------------------------------------------------
# V6 topic-targeted delivery
#
# The condition names the *launch's* attributes; the device's subscription set
# performs the match. Every condition below contains at most 4 topics against
# FCM's ceiling of 5 (3 for the class shape, plus the starlinkMuted exclusion
# on Starlink sends) -- see test_v6_topic_conditions.ConditionBudgetTests.
# --------------------------------------------------------------------------

V6_AUDIENCE_CLASSES: tuple[str, ...] = (
    "all",
    "flex",
    "strict",
    "all_w",
    "flex_w",
    "strict_w",
)

V6_NOTIFICATION_TYPES: tuple[str, ...] = (
    "twentyFourHour",
    "oneHour",
    "tenMinutes",
    "oneMinute",
    "netstampChanged",
    "webcastLive",
    "inFlight",
    "success",
    "failure",
    "partial_failure",
)

V6_BROADCAST_KINDS: tuple[str, ...] = (
    "events",
    "news",
    "announce",
)

# LL2 program id for Starlink, as it appears in the payload's comma-separated
# ``program_id`` field. Verified against the live LL2 API (launch.program[].id).
STARLINK_PROGRAM_ID = "25"

# Attribute-topic group a device subscribes to when the user mutes Starlink
# launches. Opt-out by subscription: the send condition NEGATES this topic, so
# existing subscribers need no migration -- only muted devices touch it.
V6_STARLINK_MUTED_GROUP = "starlinkMuted"

# Types that ignore the mute. Failures are rare and high-signal -- the mute
# exists to kill cadence fatigue, not news. The client copy promises this
# ("You'll still be notified if a Starlink launch fails"), so changing it is a
# product decision, not a refactor.
V6_MUTE_EXEMPT_TYPES: tuple[str, ...] = ("failure", "partial_failure")

_V6_WEBCAST_SUFFIX = "_w"


def v6_class_shape(audience_class: str) -> str:
    """Return the matching shape of a class: 'all', 'flex', or 'strict'."""
    if audience_class.endswith(_V6_WEBCAST_SUFFIX):
        return audience_class[: -len(_V6_WEBCAST_SUFFIX)]
    return audience_class


def v6_class_is_webcast_only(audience_class: str) -> bool:
    """Whether this class only wants launches that have a webcast."""
    return audience_class.endswith(_V6_WEBCAST_SUFFIX)


def get_v6_attribute_topic(env: str, group: str) -> str:
    """Attribute topic. Shared across platforms: the type topic carries platform."""
    return f"v6_{env}_{group}"


def get_v6_type_topic(env: str, platform: str, audience_class: str, notification_type: str) -> str:
    """Type topic. The audience class lives here, which is what keeps the
    classes disjoint and makes duplicate delivery structurally impossible."""
    return f"v6_{env}_{platform}_{audience_class}_{notification_type}"


def get_v6_broadcast_topic(env: str, platform: str, kind: str) -> str:
    """Broadcast topic for events / news / announce."""
    return f"v6_{env}_{platform}_{kind}"


def _v6_term(topic: str) -> str:
    return f"'{topic}' in topics"


def build_v6_condition(
    *,
    env: str,
    platform: str,
    audience_class: str,
    notification_type: str,
    agency: str | None,
    location: str | None,
    mute_starlink: bool = False,
) -> tuple[str | None, str | None]:
    """Build the FCM condition for one audience class.

    Returns ``(condition, None)`` when the send should happen, or
    ``(None, reason)`` when it must be skipped. The reason is returned rather
    than left for the caller to re-derive: this function is the only place that
    knows which check failed, and a caller reconstructing it drifts.

    ``mute_starlink``: the launch belongs to the Starlink program, so devices
    subscribed to the ``starlinkMuted`` opt-out topic are excluded -- on every
    audience class (follow-all receives all launches, so it needs the exclusion
    most), EXCEPT the ``V6_MUTE_EXEMPT_TYPES`` sends, which go to everyone.

    Skip reasons:
        unknown_type / unknown_class: no device can be subscribed to the
            resulting topic, so the condition is unsatisfiable by construction.
        unmapped_agency / unmapped_location / unmapped_attributes: the launch is
            missing an attribute this class matches on.
    """
    if notification_type not in V6_NOTIFICATION_TYPES:
        return None, "unknown_type"
    if audience_class not in V6_AUDIENCE_CLASSES:
        return None, "unknown_class"

    type_term = _v6_term(get_v6_type_topic(env, platform, audience_class, notification_type))
    shape = v6_class_shape(audience_class)

    muted_suffix = ""
    if mute_starlink and notification_type not in V6_MUTE_EXEMPT_TYPES:
        muted_term = _v6_term(get_v6_attribute_topic(env, V6_STARLINK_MUTED_GROUP))
        muted_suffix = f" && !({muted_term})"

    if shape == "all":
        return f"{type_term}{muted_suffix}", None

    agency_term = _v6_term(get_v6_attribute_topic(env, agency)) if agency else None
    location_term = _v6_term(get_v6_attribute_topic(env, location)) if location else None

    if shape == "strict":
        if not agency_term and not location_term:
            return None, "unmapped_attributes"
        if not agency_term:
            return None, "unmapped_agency"
        if not location_term:
            return None, "unmapped_location"
        return f"{type_term} && {agency_term} && {location_term}{muted_suffix}", None

    attribute_terms = [term for term in (agency_term, location_term) if term]
    if not attribute_terms:
        return None, "unmapped_attributes"
    if len(attribute_terms) == 1:
        return f"{type_term} && {attribute_terms[0]}{muted_suffix}", None
    return f"{type_term} && ({attribute_terms[0]} || {attribute_terms[1]}){muted_suffix}", None


def build_v6_broadcast_condition(env: str, platform: str, kind: str) -> str:
    """Broadcast types are gated by their own toggle only -- a single topic.

    Raises ValueError on an unknown kind. A typo here would otherwise produce a
    well-formed condition naming a topic nothing subscribes to: FCM accepts it,
    the send is recorded as a success, and the notification reaches nobody.
    """
    if kind not in V6_BROADCAST_KINDS:
        raise ValueError(f"Unknown V6 broadcast kind {kind!r}; expected one of {V6_BROADCAST_KINDS}")
    return _v6_term(get_v6_broadcast_topic(env, platform, kind))
