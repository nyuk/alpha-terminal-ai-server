from langchain_core.messages import HumanMessage, SystemMessage
from langchain_openai import ChatOpenAI

from app.domains.investment.adapter.outbound.agent.investment_agent_state import InvestmentAgentState
from app.domains.investment.adapter.outbound.agent.investment_decision_analyzer import analyze_investment_decision
from app.domains.investment.adapter.outbound.agent.log_context import aemit
from app.infrastructure.config.settings import get_settings

_SYSTEM = """당신은 투자 분석 전문 에이전트입니다.
Retrieval Agent가 수집한 원천 데이터와 구조화된 투자 판단 결과를 바탕으로 다음 항목을 분석합니다:

1. 종목 전망: 현재 상황과 향후 전망에 대한 객관적 분석
2. 리스크 요인: 투자 시 고려해야 할 위험 요소
3. 투자 포인트: 주목해야 할 주요 요인

규칙:
- 투자 추천(매수/매도) 의견은 절대 제공하지 않습니다.
- 수집된 데이터에 근거하여 분석합니다.
- 불확실한 내용은 명시합니다.
- 분석 결과는 구조화하여 작성합니다."""


async def analysis_node(state: InvestmentAgentState) -> dict:
    """Analysis 노드: Deterministic 투자 판단 + LLM 심층 분석 인사이트를 생성한다."""
    query = state["query"]
    retrieved_data = state.get("retrieved_data", "")
    parsed_query = state.get("parsed_query") or {}
    company = parsed_query.get("company")
    intent = parsed_query.get("intent", "전망 조회")

    news_signal = state.get("news_signal")
    youtube_signal = state.get("youtube_signal")

    await aemit(f"[Analysis] ▶ 시작 | query={query[:60]}")
    await aemit(
        f"[Analysis]   수집 데이터 {len(retrieved_data)}자 | "
        f"news_signal={'있음' if news_signal else '없음'} | "
        f"youtube_signal={'있음' if youtube_signal else '없음'}"
    )

    # --- 1. Deterministic 투자 판단 (rule engine + LLM rationale) ---
    verdict_result = await analyze_investment_decision(
        news_signal=news_signal,
        youtube_signal=youtube_signal,
        company=company,
        intent=intent,
    )

    # --- 2. LLM 심층 분석 ---
    settings = get_settings()
    llm = ChatOpenAI(api_key=settings.openai_api_key, model=settings.openai_model)

    verdict_summary = (
        f"\n[구조화 투자 판단]\n"
        f"direction={verdict_result['direction']} | "
        f"confidence={verdict_result['confidence']:.3f} | "
        f"verdict={verdict_result['verdict']}\n"
        f"긍정 근거: {verdict_result['reasons'].get('positive', [])}\n"
        f"부정 근거: {verdict_result['reasons'].get('negative', [])}\n"
        f"리스크: {verdict_result['risk_factors']}"
    )

    human_content = (
        f"투자 질문: {query}\n\n"
        f"수집된 원천 데이터:\n{retrieved_data}\n\n"
        f"{verdict_summary}\n\n"
        "위 정보와 구조화 투자 판단을 바탕으로 종목 전망, 리스크, 투자 포인트를 상세 분석하세요."
    )
    messages = [
        SystemMessage(content=_SYSTEM),
        HumanMessage(content=human_content),
    ]

    await aemit(f"[Analysis] → LLM 심층 분석 시작...")
    response = await llm.ainvoke(messages)
    analysis_text = response.content

    await aemit(f"[Analysis] ◀ 분석 완료 | {len(analysis_text)}자 생성")

    return {
        "analysis": analysis_text,
        "investment_verdict": verdict_result,
        "messages": [*messages, response],
    }
