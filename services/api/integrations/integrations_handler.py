from typing import Any, Dict
import requests

from config import SLACK_WEBHOOKS, DISCORD_WEBHOOKS

from .planners.rules_planner import try_rule_based_plan, enforce_plan_consistency
from .planners.llm_planner import llm_plan_message
from .schemas import MessagePlan, Integration


def plan_message(instruction: str, keep_alive: str | None = None) -> Dict[str, Any]:
    plan = try_rule_based_plan(instruction)
    if plan is not None:
        return {
            "plan": plan,
            "prompt": "None, model handled by built in rule system.",
        }

    plan, prompt = llm_plan_message(instruction, keep_alive=keep_alive)
    plan = enforce_plan_consistency(plan, instruction)

    return {
        "plan": plan,
        "prompt": prompt,
    }


def send_message(plan: MessagePlan, message: str) -> Dict[str, Any]:
    if plan.requiresReview:
        return {
            "status": "blocked",
            "integrations": [i.value for i in plan.integrations],
            "channel": plan.channel.value,
            "requiresReview": True,
            "message": message,
            "detail": "Execution blocked because requiresReview=true",
        }

    if plan.integrations == [Integration.none]:
        return {
            "status": "noop",
            "integrations": [Integration.none.value],
            "channel": plan.channel.value,
            "requiresReview": False,
            "message": message,
            "detail": "No integrations selected.",
        }

    sent_integrations = []

    for integration in plan.integrations:
        webhook_map = DISCORD_WEBHOOKS if integration == Integration.discord else SLACK_WEBHOOKS
        webhook_url = webhook_map.get(plan.channel.value)

        if not webhook_url:
            raise ValueError(
                f"No {integration.value} webhook configured for channel '{plan.channel.value}'"
            )

        payload = {"content": message} if integration == Integration.discord else {"text": message}

        r = requests.post(webhook_url, json=payload, timeout=30)
        r.raise_for_status()

        sent_integrations.append({
            "status": "sent",
            "provider": integration.value,
            "channel": plan.channel.value,
            "detail": f"{integration.value} webhook returned HTTP {r.status_code}",
        })

    return {
        "status": "sent",
        "integrations": sent_integrations,
        "channel": plan.channel.value,
        "requiresReview": False,
        "message": message,
        "detail": "Message sent successfully.",
    }