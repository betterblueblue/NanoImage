from pydantic_settings import BaseSettings
from typing import List


class Settings(BaseSettings):
    # Provider: google | proxy
    PROVIDER: str = "google"

    # Google Gemini API Key（仅服务器持有，不向前端暴露）
    GOOGLE_API_KEY: str | None = None

    # 默认图片模型名称（可在 .env 覆盖）
    GOOGLE_IMAGE_MODEL: str = "gemini-2.5-flash-image-preview"

    # Proxy（OpenAI 兼容）设置
    PROXY_BASE_URL: str = "https://api.laozhang.ai"  # 不带 /v1，代码里会拼接
    PROXY_API_KEY: str | None = None
    PROXY_MODEL: str = "gemini-2.5-flash-image-preview"  # 代理默认使用 Nano Banana（老张文档推荐）

    # 可选：失败是否禁用回退
    IMAGEN_DISABLE_FALLBACK: bool = False

    # 本地开发存储目录（生产建议使用对象存储 GCS/S3）
    STORAGE_DIR: str = "storage"

    # CORS 设置（开发环境允许所有，生产请收紧）
    ALLOWED_ORIGINS: List[str] = ["*"]

    # 任务队列（可选 Celery+Redis），此处占位
    REDIS_URL: str = "redis://localhost:6379/0"

    class Config:
        env_file = ".env"


settings = Settings()

