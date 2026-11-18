"""Environment configuration; importing this module does not create files."""
from dataclasses import dataclass
import os
from pathlib import Path


@dataclass(frozen=True)
class Settings:
    database_path: Path
    allowed_origins: tuple[str, ...] = ("http://localhost:5173", "http://127.0.0.1:5173")
    history_limit: int = 20

    @classmethod
    def from_env(cls) -> "Settings":
        default_path = Path(__file__).resolve().parents[1] / "data" / "luna.sqlite3"
        return cls(
            database_path=Path(os.environ.get("LUNA_DATABASE_PATH", str(default_path))),
            allowed_origins=tuple(origin.strip() for origin in os.environ.get(
                "LUNA_ALLOWED_ORIGINS", "http://localhost:5173,http://127.0.0.1:5173"
            ).split(",") if origin.strip()),
        )
