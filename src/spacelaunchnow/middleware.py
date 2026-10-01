import math
from datetime import datetime
from datetime import timezone as dt_timezone

from django.conf import settings
from django.utils.dateparse import parse_datetime

_FLOOR_LOOKUPS = ("__gt", "__gte")
_CEIL_LOOKUPS = ("__lt", "__lte")


class RoundTimeFiltersMiddleware:
    """Round datetime range filters on /api/ requests to a fixed bucket.

    The apps send e.g. ``net__gt=<now minus 1h>`` to the microsecond, so every
    request builds unique SQL and cachalot never gets a hit. Lower bounds round
    down and upper bounds round up, so each window only widens (by less than one
    bucket) and all clients in the same bucket share one cached query.
    """

    def __init__(self, get_response):
        self.get_response = get_response
        self.bucket = settings.TIME_FILTER_BUCKET_SECONDS

    def __call__(self, request):
        if self.bucket > 0 and request.path.startswith("/api/") and request.GET:
            self._round_params(request)
        return self.get_response(request)

    def _round_params(self, request):
        params = request.GET.copy()
        changed = False
        for key in list(params):
            if key.endswith(_FLOOR_LOOKUPS):
                ceil = False
            elif key.endswith(_CEIL_LOOKUPS):
                ceil = True
            else:
                continue
            values = params.getlist(key)
            rounded = [_round_value(value, self.bucket, ceil) for value in values]
            if rounded != values:
                params.setlist(key, rounded)
                changed = True
        if changed:
            params._mutable = False
            request.GET = params
            # Keep the raw query string in step so pagination links and any
            # URL-keyed cache see the rounded values too.
            request.META["QUERY_STRING"] = params.urlencode()


def _round_value(value, bucket, ceil):
    # Only touch values with a time part; dates and numbers pass through.
    if ":" not in value:
        return value
    try:
        parsed = parse_datetime(value)
    except ValueError:
        return value
    if parsed is None:
        return value

    aware = parsed.tzinfo is not None
    timestamp = (parsed if aware else parsed.replace(tzinfo=dt_timezone.utc)).timestamp()
    rounded = (math.ceil if ceil else math.floor)(timestamp / bucket) * bucket
    if rounded == timestamp:
        return value

    result = datetime.fromtimestamp(rounded, tz=dt_timezone.utc)
    if aware:
        return result.strftime("%Y-%m-%dT%H:%M:%SZ")
    return result.replace(tzinfo=None).strftime("%Y-%m-%dT%H:%M:%S")
