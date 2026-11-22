"""Environment configuration; importing this module does not create files."""
from dataclasses import dataclass, field
import os
from pathlib import Path

from dotenv import dotenv_values


@dataclass(frozen=True)
class Settings:
    database_path: Path
    allowed_origins: tuple[str, ...] = ("http://localhost:5173", "http://127.0.0.1:5173")
    history_limit: int = 20
    api_base_url: str = ""
    api_key: str = field(default="", repr=False)
    model_name: str = ""

    @classmethod
    def from_env(cls) -> "Settings":
        backend = Path(__file__).resolve().parents[1]
        default_path = backend / "data" / "luna.sqlite3"
        env_file = dotenv_values(backend / ".env", encoding="utf-8-sig", interpolate=False)

        def api_setting(name: str) -> str:
            return os.environ.get(name, env_file.get(name) or "").strip()

        return cls(
            database_path=Path(os.environ.get("LUNA_DATABASE_PATH", str(default_path))),
            allowed_origins=tuple(origin.strip() for origin in os.environ.get(
                "LUNA_ALLOWED_ORIGINS", "http://localhost:5173,http://127.0.0.1:5173"
            ).split(",") if origin.strip()),
            api_base_url=api_setting("LUNA_API_BASE_URL"),
            api_key=api_setting("LUNA_API_KEY"),
            model_name=api_setting("LUNA_MODEL"),
        )
