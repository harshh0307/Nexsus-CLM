from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    database_url: str = "postgresql+asyncpg://nexus:nexus_secret@localhost:5432/nexus_clm"
    openai_api_key: str = ""
    github_token: str = ""
    llm_base_url: str = "https://models.inference.ai.azure.com"
    llm_model: str = "gpt-4o-mini"

    model_config = {"env_file": ".env", "env_file_encoding": "utf-8"}


settings = Settings()
