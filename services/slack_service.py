"""Slack notification service."""

import logging
import requests
from typing import Optional


def send_slack_notification(
    webhook_url: str,
    brand_name: str,
    email: str,
    logger: logging.Logger,
    timeout: int = 10,
) -> bool:
    """Send a notification to Slack webhook about a new brand insight request.

    Args:
        webhook_url: Slack webhook URL
        brand_name: Name of the brand requested
        email: User's email address
        logger: Logger instance for logging
        timeout: Request timeout in seconds

    Returns:
        True if notification sent successfully, False otherwise
    """
    if not webhook_url or not webhook_url.strip():
        logger.debug("Slack webhook URL not configured, skipping notification")
        return False

    payload = {
        "text": f"New Brand Insight Request: {brand_name} ({email})",
        "blocks": [
            {
                "type": "header",
                "text": {
                    "type": "plain_text",
                    "text": "🎯 New Brand Insight Request",
                    "emoji": True,
                },
            },
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": f"*Brand Name:* {brand_name}\n*Email:* {email}",
                },
            },
        ],
    }

    try:
        response = requests.post(
            webhook_url,
            json=payload,
            timeout=timeout,
            headers={"Content-Type": "application/json"},
        )

        if response.status_code == 200:
            logger.info(
                f"Slack notification sent successfully for brand insight request: {brand_name}"
            )
            return True
        else:
            logger.warning(
                f"Slack notification failed with status {response.status_code}: {response.text}"
            )
            return False

    except requests.exceptions.Timeout:
        logger.warning("Slack notification timed out")
        return False
    except requests.exceptions.RequestException as e:
        logger.warning(f"Slack notification failed: {e}")
        return False
