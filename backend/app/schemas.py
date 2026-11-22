"""Public API contracts. Domain types stay independent from Pydantic."""
from typing import Literal
from uuid import UUID
from pydantic import BaseModel, ConfigDict, Field


class SendMessageRequest(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True, extra="forbid")
    client_message_id: UUID
    message: str = Field(min_length=1, max_length=4000)


class MessageResponse(BaseModel):
    id: str
    role: Literal["user", "assistant"]
    content: str
    created_at: str


class ConversationResponse(BaseModel):
    id: str
    title: str
    created_at: str


class ReplyResponse(BaseModel):
    message: MessageResponse
    sources: list[str] = Field(default_factory=list)
    provider: Literal["mock", "deepseek"] = "mock"
