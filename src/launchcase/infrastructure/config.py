import os
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class Settings:
    data_dir: Path
    database_url: str
    creative_mode: str = "mock"
    creative_url: str = "http://127.0.0.1:4311"
    creative_token: str = ""
    research_mode: str = "fake"

    @classmethod
    def from_env(cls):
        root = Path(os.getenv("LAUNCHCASE_DATA_DIR", ".launchcase")).absolute()
        return cls(
            root,
            os.getenv("LAUNCHCASE_DATABASE_URL", f"sqlite:///{root}/launchcase.db"),
            os.getenv("LAUNCHCASE_CREATIVE_ENGINE_MODE", "mock"),
            os.getenv("LAUNCHCASE_CREATIVE_ENGINE_URL", "http://127.0.0.1:4311"),
            os.getenv("LAUNCHCASE_CREATIVE_ENGINE_TOKEN", ""),
            os.getenv("LAUNCHCASE_RESEARCH_MODE", "fake"),
        )

    def prepare(self):
        if self.research_mode not in {"fake", "live"}:
            raise ValueError("Unsupported research mode")
        self.data_dir.mkdir(parents=True, exist_ok=True)
