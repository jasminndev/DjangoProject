import os
from dataclasses import dataclass

from dotenv import load_dotenv

load_dotenv()


@dataclass
class DatabaseConfig:
    DB_USER: str = os.getenv("DB_USER")
    DB_PASS: str = os.getenv("DB_PASS")
    DB_HOST: str = os.getenv("DB_HOST")
    DB_PORT: str = os.getenv("DB_PORT")
    DB_NAME: str = os.getenv("DB_NAME")

    @property
    def db_url(self):
        return f"postgresql+asyncpg://{self.DB_USER}:{self.DB_PASS}@{self.DB_HOST}:{self.DB_PORT}/{self.DB_NAME}"


@dataclass
class RedisConfig:
    CELERY_BROKER_URL: str = os.getenv("CELERY_BROKER_URL")


@dataclass
class BotConfig:
    BOT_TOKEN: str = os.getenv("BOT_TOKEN")
    BOT_USERNAME: str = os.getenv("BOT_USERNAME")
    CHANNEL_ID: str = os.getenv("CHANNEL_ID")
    CHANNEL_USERNAME: str = os.getenv("CHANNEL_USERNAME")


@dataclass
class EmailConfig:
    EMAIL_USER = os.getenv("EMAIL_USER")
    EMAIL_PASSWORD = os.getenv("EMAIL_PASSWORD")
    EMAIL_HOST = 'smtp.gmail.com'
    EMAIL_PORT = 587


@dataclass
class Payment:
    PAYMENT_PROVIDER_TOKEN = os.getenv("PAYMENT_PROVIDER_TOKEN")


@dataclass
class Configuration:
    db = DatabaseConfig()
    redis = RedisConfig()
    bot = BotConfig()
    email = EmailConfig()


conf = Configuration()
