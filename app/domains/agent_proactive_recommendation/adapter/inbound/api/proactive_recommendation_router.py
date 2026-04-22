import logging

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.domains.agent_proactive_recommendation.application.usecase.run_proactive_recommendation_usecase import (
    RunProactiveRecommendationUseCase,
)
from app.domains.market_analysis.adapter.outbound.external.langchain_qa_adapter import LangChainQAAdapter
from app.domains.market_analysis.adapter.outbound.persistence.market_data_repository_impl import (
    MarketDataRepositoryImpl,
)
from app.domains.notification.adapter.outbound.persistence.notification_repository_impl import (
    NotificationRepositoryImpl,
)
from app.domains.user_profile.adapter.outbound.persistence.user_profile_repository_impl import (
    UserProfileRepositoryImpl,
)
from app.infrastructure.auth.require_admin import require_admin
from app.infrastructure.config.settings import get_settings
from app.infrastructure.database.session import get_db

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/agent/proactive-recommendation", tags=["agent-proactive-recommendation"])


@router.post("/run")
async def run_proactive_recommendation(
    account_id: str = Depends(require_admin),
    db: Session = Depends(get_db),
):
    """능동형 추천 스케줄러 수동 트리거. 관리자 전용."""
    settings = get_settings()
    usecase = RunProactiveRecommendationUseCase(
        market_repo=MarketDataRepositoryImpl(db),
        profile_repo=UserProfileRepositoryImpl(db),
        notification_repo=NotificationRepositoryImpl(db),
        qa=LangChainQAAdapter(api_key=settings.openai_api_key, model=settings.openai_model),
    )
    sent = usecase.execute()
    logger.info("[ProactiveRecommendation] 수동 트리거 완료 — %d명 알림 전송", sent)
    return {"sent": sent}
