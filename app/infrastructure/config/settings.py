from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    mysql_user: str
    mysql_password: str
    mysql_host: str
    mysql_port: int
    mysql_database: str
    # BL-BE-54: PostgreSQL — 비정형 데이터 저장용
    pg_host: str = "localhost"
    pg_port: int = 5432
    pg_user: str = "postgres"
    pg_password: str = ""
    pg_database: str = "alphadesk_raw"
    pg_pool_size: int = 5
    pg_max_overflow: int = 20
    redis_host: str = "localhost"
    redis_port: int = 6379
    redis_password: str = ""
    auth_password: str = ""
    auth_secret: str = ""
    kakao_client_id: str = ""
    kakao_client_secret: str = ""
    kakao_redirect_uri: str = ""
    serp_api_key: str = ""
    serp_base_url: str = "https://serpapi.com/search"
    serp_timeout: float = 10.0
    finnhub_api_key: str = ""
    data_go_kr_service_key: str = ""
    twelve_data_api_key: str = ""
    # BL-BE-15: False면 히트맵 캐시는 인메모리만
    heatmap_redis_cache_enabled: bool = True
    naver_client_id: str = ""
    naver_secret: str = ""
    twitter_bearer_token: str = ""
    dart_api_key: str = ""
    openai_api_key: str = ""
    openai_model: str = "gpt-5-mini"
    # BL-BE-50: Responses API 전용 (chat.completions용 openai_model과 분리)
    openai_responses_model: str = "gpt-5-mini"
    # BL-BE-51: 추천 이유 문장 전용 (기본 gpt-5-mini)
    openai_recommendation_reason_model: str = "gpt-5-mini"
    # LangGraph 멀티 에이전트 그래프 전용 모델
    langgraph_model: str = "gpt-4.1-mini"
    youtube_api_key: str = ""
    cors_allowed_frontend_url: str = "http://localhost:3000"
    frontend_auth_callback_url: str = "http://localhost:3000/auth-callback"
    debug: bool = False

    model_config = {
        "env_file": ".env",
        "env_file_encoding": "utf-8",
    }


def get_settings() -> Settings:
    """매 호출 시 Settings 재생성 — .env 변경이 요청 핸들러 경로에 반영됨(BL-BE-16).

    주의: 모듈 import 시점에 한 번만 평가되는 전역(예: redis_client 연결 인자,
    main.settings)은 프로세스 재시작 전까지 갱신되지 않는다.
    """
    return Settings()
