from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    STRIPE_API_KEY: str
    ENV: str = "dev"
    DATABASE_URL: str
    APP_NAME: str
    STRIPE_WEBHOOK_SECRET: str
    LOG_LEVEL: str

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
    )
