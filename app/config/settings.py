from pydantic import BaseSettings


class Settings(BaseSettings):
    STRIPE_API_KEY: str
    ENV: str = "dev"
    DATABASE_URL: str

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
