from config import SLACK_WEBHOOKS
import requests


def send_message(channel: str, message: str):
    url = SLACK_WEBHOOKS.get(channel)

    if not url:
        raise ValueError(f"No Slack webhook configured for channel '{channel}'")

    r = requests.post(url, json={"text": message}, timeout=30)
    r.raise_for_status()

    return {"status": "sent", "provider": "slack"}