from functools import lru_cache

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    mysql_user: str
    mysql_password: str
    mysql_host: str
    mysql_port: int
    mysql_database: str
    redis_host: str = "localhost"
    redis_port: int = 6379
    redis_password: str = ""
    auth_password: str = ""
    kakao_client_id: str = ""
    kakao_redirect_uri: str = ""
    serp_api_key: str = ""
    dart_api_key: str = ""
    openai_api_key: str = ""
    cors_allowed_frontend_url: str = "http://localhost:3000"
    debug: bool = False

    model_config = {
        "env_file": ".env",
        "env_file_encoding": "utf-8",
    }


@lru_cache
def get_settings() -> Settings:
    return Settings()
