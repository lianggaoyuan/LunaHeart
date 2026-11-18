"""Replace adapters here without changing HTTP handlers or persistence."""
from dataclasses import replace
from .domain import AgentContext, ContextSource, Evidence, KnowledgeRetriever, Message, ModelProvider


class EmptyKnowledgeRetriever:
    def search(self, query: str) -> tuple[Evidence, ...]:
        return ()


class BasicContextSource:
    def build(self, history: tuple[Message, ...]) -> AgentContext:
        return AgentContext(history=history)


class MockModelProvider:
    """Deterministic development response, not reviewed psychological support."""
    def generate(self, message: str, context: AgentContext) -> str:
        previous = sum(item.role == "user" for item in context.history)
        return (
            f"[开发模拟回复] 已收到：{message}\n"
            f"本次带入 {previous} 条历史用户消息。聊天与存储链路已连通。\n"
            "当前未连接真实模型、专业知识库或危机处理流程，请仅使用虚构测试信息。"
        )


class AgentService:
    def __init__(self, model: ModelProvider, context_source: ContextSource,
                 retriever: KnowledgeRetriever):
        self.model = model
        self.context_source = context_source
        self.retriever = retriever

    def reply(self, message: str, history: tuple[Message, ...]) -> str:
        context = self.context_source.build(history)
        context = replace(context, evidence=self.retriever.search(message))
        # Citations are deliberately not emitted until an adapter can associate
        # actual used evidence with generated text and validate those references.
        result = self.model.generate(message, context)
        if not result.strip():
            raise ValueError("Model returned an empty response")
        return result
