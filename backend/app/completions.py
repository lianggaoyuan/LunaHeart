"""Shared transport for OpenAI-compatible text completions."""
import httpx


class ChatCompletionsClient:
    def __init__(self, base_url: str, api_key: str, completion_options: dict, setting: str):
        url = httpx.URL(base_url.rstrip("/"))
        if url.scheme != "https" or not url.host or url.userinfo or url.query or url.fragment:
            raise ValueError(f"{setting} 必须是有效的 HTTPS API 地址")
        self.endpoint = url if url.path.endswith("/chat/completions") else url.copy_with(
            path=f"{url.path.rstrip('/')}/chat/completions"
        )
        self.headers = {"Authorization": f"Bearer {api_key}"}
        self.completion_options = completion_options

    def complete(self, model: str, messages: list[dict[str, str]]) -> str:
        response = httpx.post(
            self.endpoint,
            headers=self.headers,
            json={"model": model, "messages": messages, "stream": False, **self.completion_options},
            timeout=httpx.Timeout(75.0, connect=10.0),
        )
        response.raise_for_status()
        content = response.json()["choices"][0]["message"]["content"].strip()
        if not content:
            raise ValueError("Model returned an empty response")
        return content
