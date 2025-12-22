import os
from dotenv import load_dotenv



load_dotenv()


class Settings:
    DATABASE_URL: str = os.getenv(
        "DATABASE_URL",
        "sqlite+aiosqlite:///./test.db"
    )

    SECRET_KEY: str = os.getenv("SECRET_KEY", "change-me")
    ALGORITHM: str = "HS256"

    ACCESS_TOKEN_EXPIRE_MINUTES: int = int(
        os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", 30)
    )

    REFRESH_TOKEN_EXPIRE_DAYS: int = int(
        os.getenv("REFRESH_TOKEN_EXPIRE_DAYS", 7)
    )

    MOCK_MODE: bool = os.getenv("MOCK_MODE", False) == "True"
    MOCK_WEBHOOK: bool = os.getenv("MOCK_WEBHOOK", False) == "True"

settings = Settings()
