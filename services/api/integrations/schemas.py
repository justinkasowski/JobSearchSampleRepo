from enum import Enum
from typing import List, Optional
from pydantic import BaseModel, Field


class Integration(str, Enum):
    none = "none"
    slack = "slack"
    discord = "discord"


class Channel(str, Enum):
    none = "none"
    policy = "policy"
    hr = "hr"
    sales = "sales"


class MessagePlan(BaseModel):
    integrations: List[Integration] = Field(
        description="Which integrations should receive the message."
    )
    channel: Channel = Field(
        description="Which configured target channel should receive the message."
    )
    requiresReview: bool = Field(
        default=False,
        description="Whether the plan should be manually reviewed before execution."
    )
    rationale: str = Field(
        min_length=1,
        description="Brief explanation of why this integration and channel were selected."
    )


class IntegrationPlanRequest(BaseModel):
    instruction: str = Field(
        min_length=1,
        description="Natural language user request or question."
    )
    keep_alive: Optional[str] = Field(
        default=None,
        description="Optional Ollama keep_alive override."
    )


class SendMessageRequest(BaseModel):
    plan: MessagePlan
    message: str = Field(
        min_length=1,
        description="The already-generated answer text to send."
    )


class SendMessageResponse(BaseModel):
    status: str
    integrations: List[Integration]
    channel: Channel
    requiresReview: bool
    message: str
    detail: Optional[str] = None
