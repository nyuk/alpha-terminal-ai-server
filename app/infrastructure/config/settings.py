from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    mysql_user: str
    mysql_password: str
    mysql_host: str
    mysql_port: int
    mysql_database: str
    # BL-BE-54: PostgreSQL — 비정형 데이터 저장용
    pg_host: str = "postgres"
    pg_port: int = 5432
    pg_user: str = "eddi"
    pg_password: str = ""
    pg_database: str = "appdb"
    pg_pool_size: int = 5
    pg_max_overflow: int = 20
    redis_host: str = "redis"
    redis_port: int = 6379
    redis_password: str = ""
    redis_db: int = 0
    session_expire_minutes: int = 1440
    auth_password: str = ""
    auth_secret: str = ""
    kakao_client_id: str = ""
    kakao_client_secret: str = ""
    kakao_redirect_uri: str = ""
    serp_api_key: str = ""
    serp_base_url: str = "https://serpapi.com/search"
    serp_timeout: float = 10.0
    serp_api_base_url: str = "https://serpapi.com"
    serp_api_default_engine: str = "google_news"
    serp_api_timeout_seconds: float = 10.0
    serp_api_max_retries: int = 3
    finnhub_api_key: str = ""
    data_go_kr_service_key: str = ""
    twelve_data_api_key: str = ""
    # BL-BE-15: False면 히트맵 캐시는 인메모리만
    heatmap_redis_cache_enabled: bool = True
    # 파이프라인 진행/요약 상태 저장소 — True면 Redis 기반, 실패/False면 in-memory 폴백
    pipeline_state_redis_enabled: bool = True
    # BL-BE-89: market_videos 가 이 시간보다 오래됐으면 on-demand 재수집 trigger
    market_video_stale_hours: int = 6
    naver_client_id: str = ""
    naver_secret: str = ""
    twitter_bearer_token: str = ""
    dart_api_key: str = ""
    openai_api_key: str = ""
    openai_model: str = "gpt-5-mini"
    # BL-BE-50: Responses API 전용 (chat.completions용 openai_model과 분리)
    openai_responses_model: str = "gpt-5-mini"
    # LangGraph 멀티 에이전트 그래프 전용 모델
    langgraph_model: str = "gpt-4.1-mini"
    youtube_api_key: str = ""
    cors_allowed_frontend_url: str = "http://localhost:3000"
    frontend_auth_callback_url: str = "http://localhost:3000/auth-callback"
    stock_auto_sync_enabled: bool = False
    pipeline_scheduler_enabled: bool = False
    profile_scheduler_enabled: bool = False
    proactive_briefing_scheduler_enabled: bool = False
    admin_secret_code: str = ""
    debug: bool = False
    # HTTPS 환경이 아닌 경우 false로 설정 (예: HTTP 배포, 로컬 개발)
    cookie_secure: bool = True

    model_config = {
        "env_file": ".env",
        "env_file_encoding": "utf-8",
        "extra": "ignore",
    }


def get_settings() -> Settings:
    """매 호출 시 Settings 재생성 — .env 변경이 요청 핸들러 경로에 반영됨(BL-BE-16).

    주의: 모듈 import 시점에 한 번만 평가되는 전역(예: redis_client 연결 인자,
    main.settings)은 프로세스 재시작 전까지 갱신되지 않는다.
    """
    return Settings()
