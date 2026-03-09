from typing import Any, Dict
import requests

from config import SLACK_WEBHOOKS, DISCORD_WEBHOOKS
from integrations.schemas import MessagePlan, Integration

from .planners.llm_planner import llm_plan_message
from .planners.rules_planner import try_rule_based_plan, extract_channel_matches


def plan_message(instruction: str, keep_alive: str | None = None) -> Dict[str, Any]:
    plan = try_rule_based_plan(instruction)
    if plan is not None:
        return {
            "plan": plan,
            "prompt": "None, model handled by built in rule system."
        }

    plan, prompt, raw_output = llm_plan_message(instruction, keep_alive=keep_alive)
    if len(extract_channel_matches(prompt))>1:
        plan.requiresReview = True
        plan.rationale += " [Requires review, more than one channel listed explicity]"
    return {
        "plan": plan,
        "prompt": prompt,
    }


def send_message(plan: MessagePlan, message: str) -> Dict[str, Any]:
    if plan.requiresReview:
        return {
            "status": "blocked",
            "integrations": plan.integrations,
            "channel": plan.channel,
            "requiresReview": True,
            "message": message,
            "detail": "Execution blocked because requiresReview=true",
        }

    sent_integrations = []

    for integration in plan.integrations:
        if integration == Integration.none:
            continue

        if integration == Integration.slack:
            webhook_url = SLACK_WEBHOOKS.get(plan.channel.value)
            if not webhook_url:
                raise ValueError(f"No Slack webhook configured for channel '{plan.channel.value}'")

            r = requests.post(
                webhook_url,
                json={"text": message},
                timeout=30,
            )
            r.raise_for_status()
            sent_integrations.append(Integration.slack)

        elif integration == Integration.discord:
            webhook_url = DISCORD_WEBHOOKS.get(plan.channel.value)
            if not webhook_url:
                raise ValueError(f"No Discord webhook configured for channel '{plan.channel.value}'")

            r = requests.post(
                webhook_url,
                json={"content": message},
                timeout=30,
            )
            r.raise_for_status()
            sent_integrations.append(Integration.discord)

    detail = "Message sent successfully." if sent_integrations else "No integrations selected."


    return {
        "status": "sent" if sent_integrations else "noop",
        "integrations": sent_integrations if sent_integrations else [Integration.none],
        "channel": plan.channel,
        "requiresReview": plan.requiresReview,
        "message": message,
        "detail": detail,
    }