"""Internal types and integration ports. No framework or database dependency."""
from dataclasses import dataclass, field
from typing import Literal, Protocol


@dataclass(frozen=True)
class Conversation:
    id: str
    title: str
    created_at: str


@dataclass(frozen=True)
class Message:
    id: str
    role: Literal["user", "assistant"]
    content: str
    created_at: str


@dataclass(frozen=True)
class Evidence:
    id: str
    title: str
    text: str
    url: str | None = None


@dataclass(frozen=True)
class AgentContext:
    history: tuple[Message, ...]
    profile_summary: str | None = None
    state_summary: str | None = None
    evidence: tuple[Evidence, ...] = field(default_factory=tuple)


class ModelProvider(Protocol):
    def generate(self, message: str, context: AgentContext) -> str: ...


class KnowledgeRetriever(Protocol):
    def search(self, query: str) -> tuple[Evidence, ...]: ...


class ContextSource(Protocol):
    """Future profile/state adapters must enforce their own consent rules."""
    def build(self, history: tuple[Message, ...]) -> AgentContext: ...


class AppError(Exception):
    def __init__(self, code: str, message: str, status: int = 400):
        super().__init__(message)
        self.code, self.message, self.status = code, message, status
