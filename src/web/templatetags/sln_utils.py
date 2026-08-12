# app/templatetags/sln_utils.py
from datetime import timezone as dt_timezone

from api.models import Events, Launch
from django import template

register = template.Library()


@register.filter
def get_type(value):
    if isinstance(value, Events):
        return "event"
    elif isinstance(value, Launch):
        return "launch"
    else:
        return None


# --- Launch time display -------------------------------------------------
#
# A NET is only as precise as `net_precision` says it is. Precisions that
# carry a real time-of-day get a timezone and a UTC line; coarser ones
# ("Q3 2026", "During the 2020s") get neither, because attaching a timezone
# to them would assert precision the data does not have.
#
# This table is the single source of truth for that decision. It mirrors the
# format list that used to be duplicated in getDateFormat() across the launch
# detail, mobile launch detail and event detail templates.

SHAPE_DATETIME = "datetime"
SHAPE_DATE = "date"

_DATE_FMT = "%B %d, %Y"

# precision id -> (Intl time granularity, prefix) for time-bearing precisions.
# The granularity key is consumed by launch-time.js; it deliberately carries no
# precision semantics of its own.
_TIME_BEARING = {
    0: ("hms", None),  # second
    1: ("hm", None),  # minute
    2: ("h", "NET"),  # hour
}

# Fallback when net_precision is missing or unrecognised, and the granularity
# used for launch windows (which carry no precision of their own). Minute, not
# second: the old getDateFormat() default rendered seconds, but that branch only
# fired for unknown ids, and seconds are noise on a window range.
_DEFAULT_TIME_BEARING = ("hm", None)

_UTC_TIME_FMT = {
    "hms": "%H:%M:%S",
    "hm": "%H:%M",
    "h": "%H:00",
}


def _coarse_label(utc, precision_id):
    """Render a coarse (non-time-bearing) NET. Returns None if not coarse."""
    year = utc.year
    if precision_id == 3:
        return f"Morning (local) {utc.strftime(_DATE_FMT)}"
    if precision_id == 4:
        return f"Afternoon (local) {utc.strftime(_DATE_FMT)}"
    if precision_id == 5:
        return utc.strftime(_DATE_FMT)
    if precision_id == 6:
        return f"Week of {utc.strftime(_DATE_FMT)}"
    if precision_id == 7:
        return utc.strftime("%B %Y")
    if precision_id in (8, 9, 10, 11):
        return f"Q{precision_id - 7} {year}"
    if precision_id in (12, 13):
        return f"H{precision_id - 11} {year}"
    if precision_id == 14:
        return f"NET {year}"
    if precision_id == 15:
        return f"FY {year}"
    if precision_id == 16:
        return f"During the {year // 10 * 10}s"
    return None


def launch_time_context(value, precision=None):
    """Build the context for one rendered launch time.

    `value` is an aware datetime; `precision` is a NetPrecision instance (or
    anything exposing `.id`), which may be None.
    """
    if value is None:
        return {"iso": None}

    utc = value.astimezone(dt_timezone.utc)
    precision_id = getattr(precision, "id", None)

    label = _coarse_label(utc, precision_id)
    if label is not None:
        return {
            "iso": utc.isoformat(),
            "shape": SHAPE_DATE,
            "time_parts": None,
            "prefix": None,
            "fallback": label,
        }

    time_parts, prefix = _TIME_BEARING.get(precision_id, _DEFAULT_TIME_BEARING)
    time_str = utc.strftime(_UTC_TIME_FMT[time_parts])
    prefixed = f"{prefix} {time_str}" if prefix else time_str
    return {
        "iso": utc.isoformat(),
        "shape": SHAPE_DATETIME,
        "time_parts": time_parts,
        "prefix": prefix,
        "fallback": f"{utc.strftime(_DATE_FMT)} - {prefixed} UTC",
    }


@register.inclusion_tag("web/includes/launch_time.html")
def launch_time(value, precision=None):
    """Render a launch/event NET as local time over UTC.

    Emits a <time> element carrying the UTC instant plus a fully rendered,
    always-labeled UTC fallback. launch-time.js upgrades it to viewer-local
    time; with JS unavailable the fallback stands on its own.
    """
    return launch_time_context(value, precision)
