from pathlib import Path
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    APP_NAME: str = "天权留学选校推荐引擎"
    APP_VERSION: str = "2.0.0"

    DB_PATH: str = str(Path(__file__).parent.parent.parent / "data" / "advisor.db")
    DATA_DIR: str = str(Path(__file__).parent.parent.parent / "data")
    WERS_DB_PATH: str = str(Path(__file__).parent.parent.parent.parent / "werss" / "data" / "db.db")

    HOST: str = "0.0.0.0"
    PORT: int = 3470
    WORKERS: int = 1

    CORS_ORIGINS: list[str] = ["*"]

    REQUEST_TIMEOUT: int = 300

    LLM_PROVIDER: str = "dashscope"
    LLM_API_KEY: str = ""
    LLM_BASE_URL: str = "https://dashscope.aliyuncs.com/compatible-mode/v1"
    LLM_MODEL: str = "qwen3.5-plus"

    model_config = {"env_prefix": "TIANQUAN_", "env_file": ".env"}


settings = Settings()
