from typing import Optional

from fastapi import APIRouter, Cookie, Depends, HTTPException
from sqlalchemy.orm import Session

from app.domains.auth.adapter.outbound.in_memory.redis_session_adapter import RedisSessionAdapter
from app.domains.market_analysis.adapter.outbound.external.langchain_qa_adapter import LangChainQAAdapter
from app.domains.market_analysis.adapter.outbound.external.langchain_term_explainer_adapter import (
    LangChainTermExplainerAdapter,
)
from app.domains.market_analysis.adapter.outbound.persistence.market_data_repository_impl import (
    MarketDataRepositoryImpl,
)
from app.domains.market_analysis.application.request.agent_graph_request import AgentGraphRequest
from app.domains.market_analysis.application.request.analysis_request import AnalysisQueryRequest
from app.domains.market_analysis.application.request.explain_term_request import ExplainTermRequest
from app.domains.market_analysis.application.response.agent_graph_response import AgentGraphResponse
from app.domains.market_analysis.application.response.analysis_response import AnalysisAnswerResponse
from app.domains.market_analysis.application.response.explain_term_response import ExplainTermResponse
from app.domains.market_analysis.application.usecase.analyze_market_query_usecase import (
    AnalyzeMarketQueryUseCase,
)
from app.domains.market_analysis.application.usecase.explain_term_usecase import ExplainTermUseCase
from app.domains.user_profile.adapter.outbound.persistence.mock_user_profile_repository import (
    MockUserProfileRepository,
)
from app.infrastructure.cache.redis_client import redis_client
from app.infrastructure.config.settings import get_settings
from app.infrastructure.database.session import get_db
from app.infrastructure.log_context import aemit

router = APIRouter(prefix="/market-analysis", tags=["market-analysis"])

_session_adapter = RedisSessionAdapter(redis_client)


def _resolve_account_id(
    account_id_cookie: Optional[str],
    user_token: Optional[str],
) -> Optional[int]:
    if account_id_cookie:
        try:
            return int(account_id_cookie)
        except ValueError:
            pass
    if user_token:
        session = _session_adapter.find_by_token(user_token)
        if session:
            try:
                return int(session.user_id)
            except ValueError:
                pass
    return None


@router.post("/ask", response_model=AnalysisAnswerResponse)
async def ask_market_analysis(
    request: AnalysisQueryRequest,
    db: Session = Depends(get_db),
    account_id: Optional[str] = Cookie(default=None),
    user_token: Optional[str] = Cookie(default=None),
):
    """관심종목 기반 LangChain Q&A. `user_token` 또는 `account_id` 쿠키 필요."""
    aid = _resolve_account_id(account_id, user_token)
    if aid is None:
        raise HTTPException(status_code=401, detail="로그인이 필요합니다.")

    await aemit(f"[MarketAnalysis] ▶ 분석 시작 | account_id={aid} | question={request.question[:60]}")

    settings = get_settings()
    repository = MarketDataRepositoryImpl(db)
    qa = LangChainQAAdapter(api_key=settings.openai_api_key, model=settings.openai_model)
    user_profile_repository = MockUserProfileRepository()

    await aemit(f"[MarketAnalysis][UserProfile] ▶ 프로필 조회 | account_id={aid}")
    profile = user_profile_repository.get_by_account_id(aid)
    if profile:
        await aemit(
            f"[MarketAnalysis][UserProfile] ◀ 프로필 로드 완료 | "
            f"style={profile.investment_style} | risk={profile.risk_tolerance} | "
            f"sectors={', '.join(profile.preferred_sectors)}"
        )
    else:
        await aemit(f"[MarketAnalysis][UserProfile] ⚠ 프로필 없음 → 기본 분석 적용")

    usecase = AnalyzeMarketQueryUseCase(repository, qa, user_profile_repository)
    answer = usecase.execute(account_id=aid, question=request.question)

    await aemit(
        f"[MarketAnalysis] ◀ 완료 | personalized={answer.is_personalized} | "
        f"in_scope={answer.in_scope}"
    )
    return AnalysisAnswerResponse(
        question=request.question,
        answer=answer.answer,
        in_scope=answer.in_scope,
        is_personalized=answer.is_personalized,
    )


@router.post("/explain-term", response_model=ExplainTermResponse)
async def explain_term(request: ExplainTermRequest):
    """주식/금융 용어를 쉽게 설명합니다. 로그인 불필요."""
    settings = get_settings()
    explainer = LangChainTermExplainerAdapter(api_key=settings.openai_api_key, model=settings.openai_model)
    usecase = ExplainTermUseCase(explainer)
    return usecase.execute(term=request.term, context=request.context)


@router.post("/agent-graph/run", response_model=AgentGraphResponse)
async def run_agent_graph(request: AgentGraphRequest):
    """LangGraph 멀티 에이전트 그래프 실행 (스모크 테스트 겸 진입점).

    Planner → Analyst → Reviewer 순으로 실행되며,
    Reviewer 검토 실패 시 Analyst를 최대 2회 재실행한다.
    """
    from app.infrastructure.langgraph.graph_builder import run_graph
    try:
        result = await run_graph(request.query)
        return AgentGraphResponse(**result)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"그래프 실행 실패: {e}")
