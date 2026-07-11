import secrets
from pathlib import Path
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    APP_NAME: str = "天权留学选校推荐引擎"
    APP_VERSION: str = "0.15"

    DB_PATH: str = str(Path(__file__).parent.parent.parent / "data" / "advisor.db")
    DATA_DIR: str = str(Path(__file__).parent.parent.parent / "data")
    WERS_DB_PATH: str = str(Path(__file__).parent.parent.parent.parent / "werss" / "data" / "db.db")

    HOST: str = "0.0.0.0"
    PORT: int = 3470
    WORKERS: int = 1

    # 生产环境必须在 .env 中设置具体的允许来源，如 ["https://your-frontend.com"]
    # "*" 会导致 Starlette CORSMiddleware 拒绝 Private Network Access 预检请求
    CORS_ORIGINS: list[str] = [
        "https://rongshou.github.io",
        "http://localhost:5173",
        "http://localhost:8080",
    ]

    REQUEST_TIMEOUT: int = 300

    LLM_PROVIDER: str = "dashscope"
    LLM_API_KEY: str = ""
    LLM_BASE_URL: str = "https://dashscope.aliyuncs.com/compatible-mode/v1"
    LLM_MODEL: str = "minimax-m2.7"
    LLM_FALLBACK_MODEL: str = "minimax-m2.7"
    LLM_MAX_TOKENS: int = 4096

    # 授权码体系 — 逗号分隔的合法授权码列表
    # 留空则拒绝所有请求（fail-closed）；开发时可用 AUTH_DISABLED=true 绕过
    VALID_AUTH_CODES: str = ""

    # 设为 true 可跳过所有 auth 检查（仅限开发环境）
    AUTH_DISABLED: bool = False

    model_config = {"env_prefix": "TIANQUAN_", "env_file": ".env"}

    def is_auth_code_valid(self, code: str) -> bool:
        """恒定时间比较验证码是否在有效列表中"""
        raw = self.VALID_AUTH_CODES.strip()
        if not raw:
            return False  # fail-closed: 无配置时拒绝所有
        valid_codes = [c.strip() for c in raw.split(",") if c.strip()]
        if not valid_codes:
            return False
        for valid in valid_codes:
            if secrets.compare_digest(code, valid):
                return True
        return False


settings = Settings()
