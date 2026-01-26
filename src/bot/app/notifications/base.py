import logging
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class NotificationResult:
    """Result of a notification send attempt."""

    notification_type: str
    topics: str
    result: str | None
    analytics_label: str
    error: Exception | None
