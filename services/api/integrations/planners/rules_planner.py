from typing import Optional
import re

from integrations.schemas import Integration, Channel

from integrations.schemas import MessagePlan

SEND_WORDS = {    "send",    "post",    "notify",    "message",    "share",    "publish",    "push",    "forward",
    "deliver",    "submit",}

NEGATION_PATTERNS = [    r"\bdo not send\b",    r"\bdon't send\b",    r"\bdo not post\b",    r"\bdon't post\b",
                 r"\bno need to send\b",    r"\bno need to post\b",    r"\bwithout sending\b",    r"\bwithout posting\b",]

channel_patterns = {
        Channel.hr: [r"\bhr\b",            r"\bhuman resources\b",            r"\bpeople ops\b",            r"\bpeople operations\b"],
        Channel.policy: [r"\bpolicy\b",            r"\bpolicies\b",            r"\bcompliance\b"],
        Channel.sales: [r"\bsales\b",            r"\brevenue\b",            r"\bgo to market\b",            r"\bgrowth\b"],
    }

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


def extract_channel_matches(text: str) -> list[Channel]:
    matches: list[Channel] = []

    for channel, patterns in channel_patterns.items():
        if any(re.search(pattern, text) for pattern in patterns):
            matches.append(channel)

    return matches

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
    channel_matches = extract_channel_matches(text)

    has_real_integration = any(i != Integration.none for i in integrations)

    if not send_intent and not has_real_integration:
        return MessagePlan(
            integrations=[Integration.none],
            channel=Channel.none,
            requiresReview=False,
            rationale="No send request was made.",
        )

    if not send_intent and has_real_integration: #Should be passed to LLM to see if send intent was missed
        return None

    if len(channel_matches) == 1:
        channel = channel_matches[0]
        return MessagePlan(
            integrations=integrations,
            channel=channel,
            requiresReview=False,
            rationale=f"The user explicitly requested {integrations[0]} and the {channel.value} channel (or key words triggered channel)."
        )

    return None
