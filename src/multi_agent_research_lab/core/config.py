"""Application configuration.

Keep config small and explicit. Do not read environment variables directly in agents.
"""

from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Runtime settings loaded from environment variables or `.env`."""

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    app_env: str = Field(default="local", validation_alias="APP_ENV")
    log_level: str = Field(default="INFO", validation_alias="LOG_LEVEL")

    openai_api_key: str | None = Field(default=None, validation_alias="OPENAI_API_KEY")
    openai_model: str = Field(default="gpt-4o-mini", validation_alias="OPENAI_MODEL")

    local_llm_enabled: bool = Field(default=True, validation_alias="LOCAL_LLM_ENABLED")
    local_model_path: str = Field(
        default="WEIGHT/Qwen_Qwen3.5-0.8B-Q4_K_M.gguf",
        validation_alias="LOCAL_MODEL_PATH",
    )
    local_model_n_ctx: int = Field(
        default=2048,
        ge=256,
        le=32768,
        validation_alias="LOCAL_MODEL_N_CTX",
    )
    local_model_n_gpu_layers: int = Field(default=-1, validation_alias="LOCAL_MODEL_N_GPU_LAYERS")
    local_model_max_tokens: int = Field(
        default=512,
        ge=16,
        le=2048,
        validation_alias="LOCAL_MODEL_MAX_TOKENS",
    )
    local_model_temperature: float = Field(
        default=0.2,
        ge=0.0,
        le=2.0,
        validation_alias="LOCAL_MODEL_TEMPERATURE",
    )

    langsmith_api_key: str | None = Field(default=None, validation_alias="LANGSMITH_API_KEY")
    langsmith_tracing: bool = Field(default=False, validation_alias="LANGSMITH_TRACING")
    langsmith_endpoint: str | None = Field(default=None, validation_alias="LANGSMITH_ENDPOINT")
    langsmith_project: str = Field(
        default="multi-agent-research-lab",
        validation_alias="LANGSMITH_PROJECT",
    )

    tavily_api_key: str | None = Field(default=None, validation_alias="TAVILY_API_KEY")

    max_iterations: int = Field(default=6, ge=1, le=20, validation_alias="MAX_ITERATIONS")
    timeout_seconds: int = Field(default=60, ge=5, le=600, validation_alias="TIMEOUT_SECONDS")


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """Return cached settings instance."""

    return Settings()
