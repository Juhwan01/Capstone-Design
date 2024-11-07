import os
from functools import lru_cache
from pydantic_settings import BaseSettings
from dotenv import load_dotenv
from typing import Optional

load_dotenv()

class DefaultConfig(BaseSettings):
    postgresql_endpoint: str = os.getenv("POSTGRESQL_ENDPOINT", "svc.sel5.cloudtype.app")
    postgresql_port: int = int(os.getenv("POSTGRESQL_PORT", "31872"))
    postgresql_table: str = os.getenv("POSTGRESQL_TABLE", "capstone")
    postgresql_user: str = os.getenv("POSTGRESQL_USER", "root")
    postgresql_password: str = os.getenv("POSTGRESQL_PASSWORD", "3321")
    jwt_secret_key: str = os.getenv(
        "JWT_SECRET_KEY",
        "5c2fea6305c8c209714e73b265958703e65c4b40dec4c388dddac06f3f791ec7",
    )
    jwt_algorithm: str = os.getenv("JWT_ALGORITHM", "HS256")
    jwt_expire_minutes: int = int(os.getenv("JWT_TOKEN_EXPIRE_MINUTES", "600"))
    GITHUB_CLIENT_ID: Optional[str] = os.getenv("GITHUB_CLIENT_ID")
    GITHUB_CLIENT_SECRET: Optional[str] = os.getenv("GITHUB_CLIENT_SECRET")
    GITHUB_REDIRECT_URI: Optional[str] = os.getenv("GITHUB_REDIRECT_URI")

    class Config:
        env_file = ".env"

@lru_cache
def get_config() -> DefaultConfig:
    return DefaultConfig()