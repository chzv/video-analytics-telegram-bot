from pydantic_settings import BaseSettings


class Settings(BaseSettings):

    telegram_bot_token: str
    database_url: str
    llm_api_key: str
    llm_api_base: str | None = None
    llm_model: str = "gpt-4.1-mini"

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


settings = Settings()
