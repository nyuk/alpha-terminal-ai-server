from app.domains.agent_proactive_recommendation.application.usecase import (
    run_proactive_recommendation_usecase,
)
from app.domains.market_analysis.adapter.outbound.external import langchain_qa_adapter
from app.infrastructure.langgraph.nodes import analyst, planner, researcher, reviewer


def test_ai_briefing_qa_prompt_allows_investment_decision_perspective():
    prompt = langchain_qa_adapter._SYSTEM_PROMPT

    assert "AI_BRIEFING" in prompt
    assert "매수, 매도, 보유, 관망" in prompt
    assert "추천 표현을 사용할 수 있습니다" in prompt
    assert "결론을 피하지 말고" in prompt
    assert "제공된 컨텍스트에 없는 최신 실적" in prompt
    assert "외부 실시간 시세" in prompt
    assert "구체적인 숫자를 만들지 말고" in prompt
    assert "투자 추천은 하지 마세요" not in prompt


def test_langgraph_nodes_share_ai_briefing_policy():
    prompts = [
        planner._SYSTEM_PROMPT,
        researcher._SYSTEM_PROMPT,
        analyst._SYSTEM_PROMPT,
        reviewer._SYSTEM_PROMPT,
    ]

    assert all("AI_BRIEFING" in prompt for prompt in prompts)
    assert "매수, 매도, 보유, 관망" in analyst._SYSTEM_PROMPT
    assert "결론을 피하지 말고" in analyst._SYSTEM_PROMPT
    assert "매수/매도/보유 추천" in reviewer._SYSTEM_PROMPT
    assert all("투자 추천·매수·매도 권유는 절대 하지 않습니다" not in prompt for prompt in prompts)


def test_proactive_briefing_uses_unified_ai_briefing_language():
    question = run_proactive_recommendation_usecase._QUESTION

    assert "AI_BRIEFING" in question
    assert "매수/매도/보유 추천" in question
    assert "투자 추천은 하지 마세요" not in question
