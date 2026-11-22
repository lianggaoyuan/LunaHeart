from uuid import uuid4
from fastapi.testclient import TestClient
import httpx
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


def test_deepseek_chat_passes_context_and_stores_reply(tmp_path, monkeypatch):
    requests = []
    prompt_path = tmp_path / "luna_reply.txt"
    prompt_path.write_text("初始提示词", encoding="utf-8")
    monkeypatch.setattr("app.deepseek.LUNA_PROMPT_PATH", prompt_path)

    def complete(url, **kwargs):
        assert str(url) == "https://api.deepseek.com/v1/chat/completions"
        assert kwargs["headers"]["Authorization"] == "Bearer test-key"
        requests.append(kwargs["json"])
        return httpx.Response(
            200,
            request=httpx.Request("POST", url),
            json={"choices": [{"message": {"content": "这确实挺让人担心的。"}}]},
        )

    monkeypatch.setattr(httpx, "post", complete)
    settings = Settings(
        tmp_path / "test.sqlite3",
        api_base_url="https://api.deepseek.com/v1/",
        api_key="test-key",
        model_name="test-model",
    )
    with TestClient(create_app(settings)) as client:
        assert client.get("/api/v1/health").json()["mode"] == "cloud_api"
        conversation = client.post("/api/v1/conversations").json()["id"]
        first = send(client, conversation, "我有点紧张")
        assert first.json()["provider"] == "deepseek"
        assert first.json()["message"]["content"] == "这确实挺让人担心的。"
        assert requests[0]["messages"][0] == {"role": "system", "content": "初始提示词"}

        prompt_path.write_text("更新后的提示词", encoding="utf-8")
        assert send(client, conversation, "可以继续聊聊吗").status_code == 200
        assert requests[-1]["messages"][0] == {"role": "system", "content": "更新后的提示词"}
        assert requests[-1]["messages"][1:] == [
            {"role": "user", "content": "我有点紧张"},
            {"role": "assistant", "content": "这确实挺让人担心的。"},
            {"role": "user", "content": "可以继续聊聊吗"},
        ]


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
