"""Discord webhook notification handler."""

import logging

from discord_webhook import DiscordEmbed, DiscordWebhook

from bot.app.notifications.base import NotificationResult
from spacelaunchnow import settings

logger = logging.getLogger(__name__)


class DiscordNotificationMixin:
    """Mixin for Discord webhook notifications."""

    def notify_discord(
        self,
        notification_results: list[NotificationResult] = None,
        data: dict[str, str] = None,
    ) -> None:
        """Send notification results to Discord webhook."""
        launch_name = data.get("launch_name", "Unknown") if data else "Unknown"
        launch_uuid = data.get("launch_uuid", "Unknown") if data else "Unknown"
        launch_net = data.get("launch_net", "Unknown") if data else "Unknown"
        launch_location = data.get("launch_location", "Unknown") if data else "Unknown"
        launch_image = data.get("launch_image") if data else None

        # Set up the webhook
        webhook = DiscordWebhook(
            url=settings.DISCORD_WEBHOOK,
            username="Notification Tracker",
            avatar_url="https://thespacedevs-prod.nyc3.digitaloceanspaces.com/static/home/img/launcher.png",
        )

        description = ""
        for notification_result in notification_results:
            fcm_result = {"title": None, "description": None}
            if notification_result.error:
                fcm_result["title"] = "Error"
                fcm_result["description"] = f"`{notification_result.error}`"
            if notification_result.result:
                fcm_result["title"] = "Result"
                fcm_result["description"] = f"`{notification_result.result}`"
            if notification_result.result and notification_result.error:
                fcm_result["title"] = "Result w/ Error"
                fcm_result["description"] = f"`{notification_result.result}`\n`{notification_result.error}`"

            description += (
                f"**Notification Type:** `{notification_result.notification_type}`\n"
                f"**Analytics Label:** `{notification_result.analytics_label}`\n"
                f"**Topics:** `{notification_result.topics}`\n"
                f"**{fcm_result['title']}:** {fcm_result['description']}\n"
                f"{'-' * 50}\n"
            )

        # Create the Embed
        embed = DiscordEmbed(
            title=f"🚀 {launch_name} 🚀",
            description=description,
            color="03b2f8",
        )

        # Add fields for relevant data
        embed.add_embed_field(name="Launch Name", value=launch_name, inline=False)
        embed.add_embed_field(name="Launch UUID", value=launch_uuid, inline=False)
        embed.add_embed_field(name="Launch NET", value=launch_net, inline=False)
        embed.add_embed_field(name="Launch Location", value=launch_location, inline=False)

        # Add an image for the launch if available
        if launch_image is not None:
            embed.set_thumbnail(url=launch_image)

        # Add footer with timestamp
        embed.set_footer(text="Space Launch Now - Notification Tracker")
        embed.set_timestamp()

        # Add the embed to the webhook
        webhook.add_embed(embed)

        # Execute the webhook (send the notification)
        response = webhook.execute()
        logger.info(f"Discord Notification Response: {response}")
