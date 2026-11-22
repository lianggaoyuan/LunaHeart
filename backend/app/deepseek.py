"""DeepSeek Chat Completions adapter used by the local chat prototype."""
from pathlib import Path

from .completions import ChatCompletionsClient
from .domain import AgentContext


LUNA_PROMPT_PATH = Path(__file__).resolve().parent / "prompts" / "luna_reply.txt"


def read_reply_prompt() -> str:
    prompt = LUNA_PROMPT_PATH.read_text(encoding="utf-8-sig").strip()
    if not prompt:
        raise ValueError("Luna 回复提示词不能为空")
    return prompt


class DeepSeekProvider(ChatCompletionsClient):
    def __init__(self, base_url: str, api_key: str, model: str):
        super().__init__(base_url, api_key, {"thinking": {"type": "disabled"}}, "LUNA_API_BASE_URL")
        self.model = model

    def generate(self, message: str, context: AgentContext) -> str:
        messages = [{"role": "system", "content": read_reply_prompt()}]
        messages.extend({"role": item.role, "content": item.content} for item in context.history)
        messages.append({"role": "user", "content": message})
        return self.complete(self.model, messages)
