"""Prometheus counters for the notification worker.

Exposes exact send/recipient counts to replace the log-derived (Loki)
approximations on the SLN / Notifications dashboard. The metrics HTTP
server is started once by the run_notification_service management command
and scraped by the notification-service PodMonitor.
"""

import logging

from prometheus_client import Counter, start_http_server

logger = logging.getLogger(__name__)

# platform: android|ios, category: launch|news|event|custom,
# result: success|error
NOTIFICATIONS_SENT = Counter(
    "sln_notifications_sent_total",
    "FCM notification send attempts by platform, category, and result.",
    ["platform", "category", "result"],
)

# Incremented from the FCM response's success count when the response
# reports one (topic sends usually do not — then only the send counter moves).
NOTIFICATION_RECIPIENTS = Counter(
    "sln_notification_recipients_total",
    "Recipients reported by FCM responses, by platform and category.",
    ["platform", "category"],
)


def record_send(platform: str, category: str, success: bool, result=None) -> None:
    """Record one FCM send attempt beside the existing log lines.

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
