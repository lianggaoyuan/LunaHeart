import logging
from .agent import AgentService
from .domain import AppError, Message
from .repository import ChatRepository

logger = logging.getLogger(__name__)


class ChatService:
    def __init__(self, repository: ChatRepository, agent: AgentService, history_limit: int):
        self.repository, self.agent, self.history_limit = repository, agent, history_limit

    def send(self, conversation_id: str, request_id: str, text: str) -> Message:
        history = self.repository.history(conversation_id)
        existing = self.repository.existing(conversation_id, request_id, text)
        if existing:
            return existing
        try:
            reply = self.agent.reply(text, history[-self.history_limit:])
        except Exception:
            # Do not log prompts, user text, or provider errors containing credentials.
            logger.warning("Agent generation failed")
            raise AppError("generation_failed", "回复生成失败，请重试", 503) from None
        return self.repository.save_exchange(conversation_id, request_id, text, reply, len(history))
