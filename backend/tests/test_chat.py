from uuid import uuid4
from fastapi.testclient import TestClient
from app.config import Settings
from app.main import create_app


def send(client, conversation_id, text="你好", request_id=None):
    return client.post(f"/api/v1/conversations/{conversation_id}/messages", json={
        "message": text, "client_message_id": request_id or str(uuid4())})


def test_history_is_persistent_and_conversations_do_not_mix(tmp_path):
    settings = Settings(tmp_path / "test.sqlite3")
    with TestClient(create_app(settings)) as client:
        first = client.post("/api/v1/conversations").json()["id"]
        second = client.post("/api/v1/conversations").json()["id"]
        assert send(client, first).status_code == 200
        assert send(client, first, "继续").status_code == 200
        assert client.get(f"/api/v1/conversations/{second}/messages").json() == []
    with TestClient(create_app(settings)) as client:
        history = client.get(f"/api/v1/conversations/{first}/messages").json()
        assert len(history) == 4
        assert "1 条历史用户消息" in history[-1]["content"]


def test_retry_is_idempotent_and_changed_payload_is_rejected(tmp_path):
    with TestClient(create_app(Settings(tmp_path / "test.sqlite3"))) as client:
        conversation = client.post("/api/v1/conversations").json()["id"]
        request_id = str(uuid4())
        first = send(client, conversation, request_id=request_id)
        assert send(client, conversation, request_id=request_id).json() == first.json()
        assert send(client, conversation, "另一条消息", request_id).status_code == 409
        assert len(client.get(f"/api/v1/conversations/{conversation}/messages").json()) == 2


def test_provider_failure_does_not_save_half_an_exchange(tmp_path):
    class BrokenModel:
        def generate(self, message, context):
            raise TimeoutError()
    with TestClient(create_app(Settings(tmp_path / "test.sqlite3"), BrokenModel())) as client:
        conversation = client.post("/api/v1/conversations").json()["id"]
        assert send(client, conversation).status_code == 503
        assert client.get(f"/api/v1/conversations/{conversation}/messages").json() == []


def test_validation_and_missing_conversation(tmp_path):
    with TestClient(create_app(Settings(tmp_path / "test.sqlite3"))) as client:
        assert send(client, str(uuid4())).status_code == 404
        conversation = client.post("/api/v1/conversations").json()["id"]
        result = send(client, conversation, "  ")
        assert result.status_code == 422
        assert result.json()["error"]["code"] == "invalid_request"


def test_stale_generation_cannot_overwrite_newer_history(tmp_path):
    from app.repository import ChatRepository
    from app.domain import AppError
    import pytest
    repository = ChatRepository(tmp_path / "test.sqlite3")
    repository.initialize()
    conversation = repository.create_conversation()
    repository.save_exchange(conversation.id, str(uuid4()), "first", "reply", 0)
    with pytest.raises(AppError, match="会话已更新"):
        repository.save_exchange(conversation.id, str(uuid4()), "stale", "reply", 0)
    assert len(repository.history(conversation.id)) == 2
