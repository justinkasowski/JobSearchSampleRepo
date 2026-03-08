from config import DISCORD_WEBHOOKS
import requests


def send_message(channel: str, message: str):
    url = DISCORD_WEBHOOKS.get(channel)

    if not url:
        raise ValueError(f"No Discord webhook configured for channel '{channel}'")

    r = requests.post(url, json={"content": message}, timeout=30)
    r.raise_for_status()

    return {"status": "sent", "provider": "discord"}