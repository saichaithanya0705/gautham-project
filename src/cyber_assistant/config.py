from functools import lru_cache
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env", env_file_encoding="utf-8-sig", extra="ignore"
    )

    app_env: str = "development"
    database_path: Path = Path("data/cicids2017_demo.sqlite3")
    synapt_provider_id: str = ""
    synapt_mcp_url: str = ""
    synapt_auth_base: str = ""
    synapt_username: str = ""
    synapt_password: str = ""
    synapt_ca_bundle: str = ""
    synapt_top_k: int = 5
    synapt_graph_hops: int = 2

    # External LLM / Judge Configuration (OpenAI, OpenRouter, Anthropic)
    openai_api_key: str = ""
    openai_base_url: str = ""
    openai_model: str = "gpt-4o-mini"
    openrouter_api_key: str = ""
    openrouter_base_url: str = "https://openrouter.ai/api/v1"
    openrouter_model: str = "meta-llama/llama-3.3-70b-instruct:free"
    anthropic_api_key: str = ""
    anthropic_model: str = "claude-3-5-haiku-20241022"


@lru_cache
def get_settings() -> Settings:
    return Settings()
