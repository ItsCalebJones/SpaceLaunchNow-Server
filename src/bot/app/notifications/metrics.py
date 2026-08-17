"""Prometheus counters for the notification worker.

Exposes exact send/recipient counts to replace the log-derived (Loki)
approximations on the SLN / Notifications dashboard. The metrics HTTP
server is started once by the run_notification_service management command
and scraped by the notification-service PodMonitor.
"""

import logging

from prometheus_client import Counter, start_http_server

logger = logging.getLogger(__name__)

# platform: android|ios, category: launch|news|event|custom, result: success|error
#
# V5 only. V6 deliberately does NOT share this counter: V6 fans one logical
# notification out across up to 12 sends, so mixing the two would multiply this
# series by ~7x with no change in delivery and would dilute the dashboard's
# error ratio (a total V5 outage during dual-send would read as ~14% errors
# instead of 100%). V6 gets its own counter below.
NOTIFICATIONS_SENT = Counter(
    "sln_notifications_sent_total",
    "V5 FCM notification send attempts by platform, category, and result.",
    ["platform", "category", "result"],
)

# The V6 equivalent, kept separate so each scheme's rate is readable on its own
# and so dual-send does not distort either one. audience_class is the V6 class
# name, or "broadcast" for events/news/announce.
V6_NOTIFICATIONS_SENT = Counter(
    "sln_v6_notifications_sent_total",
    "V6 FCM notification send attempts by platform, category, result, and audience class.",
    ["platform", "category", "result", "audience_class"],
)

# Incremented from the FCM response's success count when the response
# reports one (topic sends usually do not — then only the send counter moves).
NOTIFICATION_RECIPIENTS = Counter(
    "sln_notification_recipients_total",
    "Recipients reported by FCM responses, by platform and category.",
    ["platform", "category"],
)

# V6 sends not attempted. "no_webcast" is the expected, high-volume reason —
# webcast-only classes are skipped for launches with no webcast, which is what
# makes V6 volume per launch swing between 6 and 12. The unknown_*/unmapped_*
# reasons indicate a real defect: a caller passed a type or class that no device
# can be subscribed to, or a launch reached dispatch with no agency/location.
NOTIFICATION_SENDS_SKIPPED = Counter(
    "sln_notification_sends_skipped_total",
    "V6 sends skipped because the audience-class condition was unsatisfiable or inapplicable.",
    ["platform", "audience_class", "reason"],
)

# A launch whose agency or location is absent from the curated group tables and
# fell through to the catch-all group. This is the signal the group tables have
# a gap: the send still happens, but only the catch-all subscribers match it.
NOTIFICATION_GROUP_FALLBACKS = Counter(
    "sln_notification_group_fallbacks_total",
    "Launches whose agency or location resolved to the catch-all group.",
    ["kind"],
)


def record_send(platform: str, category: str, success: bool, result=None) -> None:
    """Record one V5 FCM send attempt beside the existing log lines.

    Args:
        platform: "android" or "ios".
        category: "launch", "news", "event", or "custom".
        success: whether the send raised (False) or returned (True).
        result: the raw FCM response; used to extract a recipient count
            when the response carries one.
    """
    NOTIFICATIONS_SENT.labels(
        platform=platform,
        category=category,
        result="success" if success else "error",
    ).inc()
    if success:
        recipients = _extract_success_count(result)
        if recipients > 0:
            NOTIFICATION_RECIPIENTS.labels(platform=platform, category=category).inc(recipients)


def record_v6_send(platform: str, category: str, success: bool, audience_class: str) -> None:
    """Record one V6 FCM send attempt.

    No recipient count: every V6 send is a topic-condition send, and those
    responses carry only a message name. Leaving NOTIFICATION_RECIPIENTS to V5
    keeps that panel meaning one thing for the whole dual-send window.
    """
    V6_NOTIFICATIONS_SENT.labels(
        platform=platform,
        category=category,
        result="success" if success else "error",
        audience_class=audience_class,
    ).inc()


def record_skip(platform: str, audience_class: str, reason: str) -> None:
    """Record a V6 send that was not attempted."""
    NOTIFICATION_SENDS_SKIPPED.labels(platform=platform, audience_class=audience_class, reason=reason).inc()


def record_group_fallback(kind: str) -> None:
    """Record an agency/location that fell through to its catch-all group.

    Args:
        kind: "agency" or "location".
    """
    NOTIFICATION_GROUP_FALLBACKS.labels(kind=kind).inc()


def _extract_success_count(result) -> int:
    """Best-effort extraction of a success/recipient count from an FCM response.

    Topic-condition sends return {"name": "projects/.../messages/..."} with no
    count; device-group/multicast style responses carry a "success" integer.
    """
    if isinstance(result, dict):
        value = result.get("success")
        if isinstance(value, bool):
            return int(value)
        if isinstance(value, (int, float)):
            return int(value)
    return 0


def start_metrics_server(port: int) -> None:
    """Start the prometheus_client HTTP server (call once at startup)."""
    start_http_server(port)
    logger.info(f"Prometheus metrics server listening on port {port}")
