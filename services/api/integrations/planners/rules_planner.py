from typing import Optional
import re

from integrations.schemas import MessagePlan, Integration, Channel


SEND_WORDS = {"send", "post", "notify", "message", "share", "publish", "push", "forward", "deliver", "submit",}

NEGATION_PATTERNS = [r"\bdo not send\b",    r"\bdon't send\b",    r"\bdo not post\b",    r"\bdon't post\b",
    r"\bno need to send\b",    r"\bno need to post\b",    r"\bwithout sending\b",    r"\bwithout posting\b",]

CHANNEL_PATTERNS = {
    Channel.hr: [r"\bhr\b",        r"\bhuman resources\b",        r"\bpeople ops\b",        r"\bpeople operations\b"],
    Channel.policy: [r"\bpolicy\b",        r"\bpolicies\b",        r"\bcompliance\b"],
    Channel.sales: [r"\bsales\b",        r"\brevenue\b",        r"\bgo to market\b",        r"\bgrowth\b"]
}


def _normalize_instruction(text: str) -> str:
    text = text.strip().lower()
    text = re.sub(r"[_/|,;:()\[\]{}]+", " ", text)
    text = re.sub(r"\s+", " ", text)
    return text


def _detect_send_intent(text: str) -> bool:
    return (
        not any(re.search(pattern, text) for pattern in NEGATION_PATTERNS)
        and any(re.search(rf"\b{re.escape(word)}\b", text) for word in SEND_WORDS)
    )


def _detect_integrations(text: str) -> list[Integration]:
    integrations = [
        integration
        for integration in (Integration.slack, Integration.discord)
        if re.search(rf"\b{integration.value}\b", text)
    ]
    return integrations or [Integration.none]


def _detect_channels(text: str) -> list[Channel]:
    return [
        channel
        for channel, patterns in CHANNEL_PATTERNS.items()
        if any(re.search(pattern, text) for pattern in patterns)
    ]


def _build_rationale(integrations: list[Integration], channel_matches: list[Channel]) -> str:
    integration_names = [i.value for i in integrations if i != Integration.none]

    if not integration_names:
        return "No send request was made."

    if len(channel_matches) == 0:
        if len(integration_names) == 1:
            return f"The user explicitly requested {integration_names[0]} but did not specify a channel."
        return f"The user explicitly requested {', '.join(integration_names)} but did not specify a channel."

    if len(channel_matches) > 1:
        return "The user referenced multiple possible channels, so manual review is required."

    if len(integration_names) == 1:
        return f"The user explicitly requested {integration_names[0]} and the {channel_matches[0].value} channel."

    return f"The user explicitly requested {', '.join(integration_names)} and the {channel_matches[0].value} channel."


def try_rule_based_plan(instruction: str) -> Optional[MessagePlan]:
    text = _normalize_instruction(instruction)

    send_intent = _detect_send_intent(text)
    integrations = _detect_integrations(text)
    channel_matches = _detect_channels(text)

    has_real_integration = any(i != Integration.none for i in integrations)

    if not send_intent and not has_real_integration:
        return MessagePlan(
            integrations=[Integration.none],
            channel=Channel.none,
            requiresReview=False,
            rationale="No send request was made.",
        )

    if not send_intent and has_real_integration:
        return None

    if len(channel_matches) == 1:
        return MessagePlan(
            integrations=integrations,
            channel=channel_matches[0],
            requiresReview=False,
            rationale=_build_rationale(integrations, channel_matches),
        )

    if len(channel_matches) == 0:
        return MessagePlan(
            integrations=integrations,
            channel=Channel.none,
            requiresReview=True,
            rationale=_build_rationale(integrations, channel_matches),
        )

    return MessagePlan(
        integrations=integrations,
        channel=Channel.none,
        requiresReview=True,
        rationale=_build_rationale(integrations, channel_matches),
    )


def enforce_plan_consistency(plan: MessagePlan, instruction: str) -> MessagePlan:
    text = _normalize_instruction(instruction)
    channel_matches = _detect_channels(text)
    has_real_integration = any(i != Integration.none for i in plan.integrations)

    if not has_real_integration:
        plan.integrations = [Integration.none]
        plan.channel = Channel.none
        plan.requiresReview = False
        plan.rationale = "No send request was made."
        return plan

    if len(channel_matches) == 0:
        plan.channel = Channel.none
        plan.requiresReview = True
        plan.rationale = "The user requested an integration but did not specify a channel."
        return plan

    if len(channel_matches) > 1:
        plan.channel = Channel.none
        plan.requiresReview = True
        plan.rationale = "The user referenced multiple possible channels, so manual review is required."
        return plan

    plan.channel = channel_matches[0]
    return plan