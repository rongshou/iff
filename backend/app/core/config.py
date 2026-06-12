from pathlib import Path
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    APP_NAME: str = "天权留学选校推荐引擎"
    APP_VERSION: str = "2.0.0"

    DB_PATH: str = str(Path(__file__).parent.parent.parent / "data" / "advisor.db")
    DATA_DIR: str = str(Path(__file__).parent.parent.parent / "data")

    HOST: str = "0.0.0.0"
    PORT: int = 3470
    WORKERS: int = 1

    CORS_ORIGINS: list[str] = ["*"]

    REQUEST_TIMEOUT: int = 300

    model_config = {"env_prefix": "TIANQUAN_", "env_file": ".env"}


settings = Settings()
