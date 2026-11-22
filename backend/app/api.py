"""HTTP translation only; orchestration lives in ChatService."""
from dataclasses import asdict
from uuid import UUID
from fastapi import APIRouter
from .repository import ChatRepository
from .schemas import ConversationResponse, MessageResponse, ReplyResponse, SendMessageRequest
from .service import ChatService


def create_router(repository: ChatRepository, service: ChatService, cloud_api: bool = False) -> APIRouter:
    router = APIRouter(prefix="/api/v1")

    @router.get("/health")
    def health():
        return {"status": "ok", "mode": "cloud_api" if cloud_api else "local_mock"}

    @router.get("/conversations", response_model=list[ConversationResponse])
    def list_conversations():
        return [asdict(item) for item in repository.list_conversations()]

    @router.post("/conversations", response_model=ConversationResponse, status_code=201)
    def create_conversation():
        return asdict(repository.create_conversation())

    @router.get("/conversations/{conversation_id}/messages", response_model=list[MessageResponse])
    def history(conversation_id: UUID):
        return [asdict(item) for item in repository.history(str(conversation_id))]

    @router.post("/conversations/{conversation_id}/messages", response_model=ReplyResponse)
    def send(conversation_id: UUID, payload: SendMessageRequest):
        message = service.send(str(conversation_id), str(payload.client_message_id), payload.message)
        provider = "deepseek" if cloud_api and not message.content.startswith("[开发模拟回复]") else "mock"
        return ReplyResponse(message=MessageResponse(**asdict(message)), provider=provider)

    return router
