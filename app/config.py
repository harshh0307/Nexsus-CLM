from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    database_url: str = "postgresql+asyncpg://nexus:nexus_secret@localhost:5432/nexus_clm"
    openai_api_key: str = ""
    github_token: str = ""
    llm_base_url: str = "https://models.inference.ai.azure.com"
    llm_model: str = "gpt-4o-mini"
    embedding_model: str = "text-embedding-3-small"
    embedding_url: str = "https://models.inference.ai.azure.com"
    jwt_secret: str = "change-me-in-production"
    jwt_algorithm: str = "HS256"
    jwt_expire_minutes: int = 60
    reset_token_expire_minutes: int = 15
    dev_mode: bool = True

    model_config = {"env_file": ".env", "env_file_encoding": "utf-8"}


settings = Settings()
