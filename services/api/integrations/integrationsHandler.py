from typing import Any, Dict, Optional

import re
import requests
from pydantic import ValidationError

from config import (
    MODEL,
    OLLAMA_KEEP_ALIVE,
    OLLAMA_URL,
    SLACK_WEBHOOKS,
    DISCORD_WEBHOOKS,
    INTEGRATIONS_PROMPT
)

from integrations.schemas import MessagePlan, Integration, Channel



def get_message_plan_schema() -> Dict[str, Any]:
    return MessagePlan.model_json_schema()

def _call_ollama_json(prompt: str, keep_alive: str | None = None) -> str:
    r = requests.post(
        OLLAMA_URL,
        json={
            "model": MODEL,
            "prompt": prompt,
            "stream": False,
            "keep_alive": keep_alive or OLLAMA_KEEP_ALIVE,
        },
        timeout=300,
    )
    r.raise_for_status()
    data = r.json()
    return data.get("response", "").strip()


def _clean_llm_json(raw_text: str) -> str:
    text = raw_text.strip()

    if text.startswith("```json"):
        text = text[len("```json"):].strip()
    elif text.startswith("```"):
        text = text[len("```"):].strip()

    if text.endswith("```"):
        text = text[:-3].strip()

    return text


SEND_WORDS = {
    "send",
    "post",
    "notify",
    "message",
    "share",
    "publish",
    "push",
    "forward",
    "deliver",
    "submit",
}

NEGATION_PATTERNS = [
    r"\bdo not send\b",
    r"\bdon't send\b",
    r"\bdo not post\b",
    r"\bdon't post\b",
    r"\bno need to send\b",
    r"\bno need to post\b",
    r"\bwithout sending\b",
    r"\bwithout posting\b",
]


def _normalize_instruction(text: str) -> str:
    text = text.strip().lower()
    text = re.sub(r"[_/|,;:()\[\]{}]+", " ", text)
    text = re.sub(r"\s+", " ", text)
    return text


def _contains_send_intent(text: str) -> bool:
    if any(re.search(pattern, text) for pattern in NEGATION_PATTERNS):
        return False

    return any(re.search(rf"\b{re.escape(word)}\b", text) for word in SEND_WORDS)


def _extract_integrations(text: str) -> list[Integration]:
    integrations: list[Integration] = []

    if re.search(r"\bslack\b", text):
        integrations.append(Integration.slack)

    if re.search(r"\bdiscord\b", text):
        integrations.append(Integration.discord)

    if not integrations:
        return [Integration.none]

    return integrations


def _extract_channel_matches(text: str) -> list[Channel]:
    channel_patterns = {
        Channel.hr: [
            r"\bhr\b",
            r"\bhuman resources\b",
            r"\bpeople ops\b",
            r"\bpeople operations\b",
        ],
        Channel.policy: [
            r"\bpolicy\b",
            r"\bpolicies\b",
            r"\bcompliance\b",
        ],
        Channel.sales: [
            r"\bsales\b",
            r"\brevenue\b",
            r"\bgo to market\b",
            r"\bgrowth\b",
        ],
    }

    matches: list[Channel] = []

    for channel, patterns in channel_patterns.items():
        if any(re.search(pattern, text) for pattern in patterns):
            matches.append(channel)

    return matches


def _build_explicit_rationale(
    integrations: list[Integration],
    channel: Channel,
    requires_review: bool,
) -> str:
    integration_names = [i.value for i in integrations if i != Integration.none]

    if not integration_names:
        return "No send request was made."

    if requires_review and channel == Channel.none:
        if len(integration_names) == 1:
            return f"The user explicitly requested {integration_names[0]} but did not specify a channel."
        return f"The user explicitly requested {', '.join(integration_names)} but did not specify a channel."

    if len(integration_names) == 1:
        return f"The user explicitly requested {integration_names[0]} and the {channel.value} channel (or key words triggered channel)."

    if len(integration_names) == 2:
        return f"The user explicitly requested {integration_names[0]}, {integration_names[1]}, and the {channel.value} channel."

    return "The user explicitly requested a supported integration and channel."


def try_rule_based_plan(instruction: str) -> Optional[MessagePlan]:
    """
    Deterministic fast path for obvious integration instructions.

    Returns:
        - MessagePlan when the instruction is explicit enough to resolve safely
        - None when the wording is too ambiguous and should fall back to LLM planning
    """
    text = _normalize_instruction(instruction)

    send_intent = _contains_send_intent(text)
    integrations = _extract_integrations(text)
    channel_matches = _extract_channel_matches(text)

    has_real_integration = any(i != Integration.none for i in integrations)

    # Case 1: no explicit send/post/share intent and no platform mention
    # Safe to short-circuit to "no action requested"
    if not send_intent and not has_real_integration:
        return MessagePlan(
            integrations=[Integration.none],
            channel=Channel.none,
            requiresReview=False,
            rationale="No send request was made.",
        )

    # Case 2: platform mentioned but no send intent
    # Example: "is slack configured?" or "does discord work?"
    # Let the LLM handle these because mention != action request.
    if not send_intent and has_real_integration:
        return None

    # Case 3: explicit send intent and exactly one channel match
    if len(channel_matches) == 1:
        channel = channel_matches[0]
        return MessagePlan(
            integrations=integrations,
            channel=channel,
            requiresReview=False,
            rationale=_build_explicit_rationale(
                integrations=integrations,
                channel=channel,
                requires_review=False,
            ),
        )

    return None

def enforce_plan_consistency(plan: MessagePlan, instruction: str) -> MessagePlan:
    rationale = (plan.rationale or "").lower()
    text = _normalize_instruction(instruction)
    channel_matches = _extract_channel_matches(text)
    has_real_integration = any(i != Integration.none for i in plan.integrations)

    ambiguous_words = [
        "ambiguous",
        "unclear",
        "not clear",
        "unsure",
        "uncertain",
        "multiple possible",
        "manual review",
        "cannot determine",
        "did not specify",
    ]

    if any(word in rationale for word in ambiguous_words):
        plan.requiresReview = True

    if has_real_integration:
        if len(channel_matches) == 0:
            if "user specified a channel" in rationale or "explicitly requested" in rationale:
                plan.rationale = "The user requested an integration but did not specify a channel."
            plan.requiresReview = True

        elif len(channel_matches) > 1:
            plan.requiresReview = True
            plan.rationale = "The user referenced multiple possible channels, so manual review is required."

        elif len(channel_matches) == 1:
            actual_channel = channel_matches[0]
            if plan.channel != actual_channel:
                plan.channel = actual_channel
                plan.rationale = f"The user explicitly requested the {actual_channel.value} channel."

    return plan
def plan_message(instruction: str, keep_alive: str | None = None) -> Dict[str, Any]:
    plan = try_rule_based_plan(instruction)
    if plan is not None:
        return {
            "plan": plan,
            "prompt": "None, model handled by built in rule system."
        }

    prompt = f"""{INTEGRATIONS_PROMPT}

USER QUESTION:
{instruction}
"""

    raw_output = _call_ollama_json(prompt, keep_alive=keep_alive)
    cleaned_output = _clean_llm_json(raw_output)

    try:
        plan = MessagePlan.model_validate_json(cleaned_output)
    except ValidationError as e:
        raise ValueError(
            f"LLM returned invalid MessagePlan JSON.\nRaw output:\n{raw_output}\n\nValidation error:\n{e}"
        )

    try:
        plan = enforce_plan_consistency(plan, instruction)
    except Exception as e:
        raise ValueError(
            f"Parsed MessagePlan successfully, but enforce_plan_consistency failed.\n"
            f"Raw output:\n{raw_output}\n\n"
            f"Parsed plan:\n{plan.model_dump()}\n\n"
            f"Error type: {type(e).__name__}\n"
            f"Error: {e!r}"
        )

    return {
        "plan": plan,
        "prompt": prompt,
    }

def _send_slack_message(channel: str, message: str) -> Dict[str, Any]:
    webhook_url = SLACK_WEBHOOKS.get(channel)
    if not webhook_url:
        raise ValueError(f"No Slack webhook configured for channel '{channel}'")

    r = requests.post(
        webhook_url,
        json={"text": message},
        timeout=30,
    )
    r.raise_for_status()

    return {
        "status": "sent",
        "provider": "slack",
        "channel": channel,
        "detail": f"Slack webhook returned HTTP {r.status_code}",
    }


def _send_discord_message(channel: str, message: str) -> Dict[str, Any]:
    webhook_url = DISCORD_WEBHOOKS.get(channel)
    if not webhook_url:
        raise ValueError(f"No Discord webhook configured for channel '{channel}'")

    r = requests.post(
        webhook_url,
        json={"content": message},
        timeout=30,
    )
    r.raise_for_status()

    return {
        "status": "sent",
        "provider": "discord",
        "channel": channel,
        "detail": f"Discord webhook returned HTTP {r.status_code}",
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
        elif integration == Integration.slack:
            _send_slack_message(plan.channel.value, message)
            sent_integrations.append(Integration.slack)
        elif integration == Integration.discord:
            _send_discord_message(plan.channel.value, message)
            sent_integrations.append(Integration.discord)

    return {
        "status": "sent" if sent_integrations else "noop",
        "integrations": sent_integrations if sent_integrations else [Integration.none],
        "channel": plan.channel,
        "requiresReview": plan.requiresReview,
        "message": message,
        "detail": "Message sent successfully." if sent_integrations else "No integrations selected.",
    }