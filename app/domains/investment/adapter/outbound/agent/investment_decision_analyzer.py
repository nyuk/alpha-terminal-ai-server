"""투자 판단 결정 분석기.

direction / confidence / verdict : deterministic rule 기반 (LLM 개입 없음)
reasons / risk_factors           : LLM rationale 생성

규칙:
    impact 가중치 : high=3.0, medium=2.0, low=1.0
    news_score    = Σ pos_impact - Σ neg_impact
    direction     : news_score > 2.0 → bullish
                    news_score < -2.0 → bearish
                    else → neutral
    confidence    = sigmoid(1.0 * |news_score| + 0.5 * |sentiment_score|)
    verdict       : bullish + confidence > 0.6 → buy
                    bearish + confidence > 0.6 → sell
                    else → hold

입력 신호 부족 시 보수적 fallback: verdict=hold, confidence=0.3
"""
import json
import math
import re
from typing import Optional

from langchain_core.messages import HumanMessage, SystemMessage
from langchain_openai import ChatOpenAI

from app.domains.investment.adapter.outbound.agent.log_context import aemit
from app.infrastructure.config.settings import get_settings

# ---------------------------------------------------------------------------
# 가중치 상수
# ---------------------------------------------------------------------------
IMPACT_WEIGHTS: dict[str, float] = {"high": 3.0, "medium": 2.0, "low": 1.0}
NEWS_SCORE_THRESHOLD = 2.0
W_NEWS = 1.0
W_SENTIMENT = 0.5
VERDICT_CONFIDENCE_THRESHOLD = 0.6

# ---------------------------------------------------------------------------
# 보수적 fallback
# ---------------------------------------------------------------------------
_FALLBACK: dict = {
    "direction": "neutral",
    "confidence": 0.3,
    "verdict": "hold",
    "reasons": {"positive": [], "negative": []},
    "risk_factors": ["입력 신호 부족으로 보수적 판단 적용"],
}


# ---------------------------------------------------------------------------
# Deterministic rule engine
# ---------------------------------------------------------------------------

def _sigmoid(x: float) -> float:
    return 1.0 / (1.0 + math.exp(-x))


def _compute_news_score(news_signal: dict) -> float:
    """뉴스 이벤트 impact 가중치 합산 → news_score."""
    pos = sum(
        IMPACT_WEIGHTS.get(e.get("impact", "low"), 1.0)
        for e in news_signal.get("positive_events", [])
    )
    neg = sum(
        IMPACT_WEIGHTS.get(e.get("impact", "low"), 1.0)
        for e in news_signal.get("negative_events", [])
    )
    return pos - neg


def compute_direction_confidence_verdict(
    news_signal: dict,
    youtube_signal: dict,
) -> tuple[str, float, str]:
    """Deterministic rule 기반 (direction, confidence, verdict) 산출.

    동일 입력 → 동일 결과 보장.
    """
    news_score = _compute_news_score(news_signal)
    sentiment_score = float(youtube_signal.get("sentiment_score", 0.0))

    # direction (news_score 기준)
    if news_score > NEWS_SCORE_THRESHOLD:
        direction = "bullish"
    elif news_score < -NEWS_SCORE_THRESHOLD:
        direction = "bearish"
    else:
        direction = "neutral"

    # confidence (sigmoid 정규화)
    raw = W_NEWS * abs(news_score) + W_SENTIMENT * abs(sentiment_score)
    confidence = round(_sigmoid(raw), 4)

    # verdict
    if direction == "bullish" and confidence > VERDICT_CONFIDENCE_THRESHOLD:
        verdict = "buy"
    elif direction == "bearish" and confidence > VERDICT_CONFIDENCE_THRESHOLD:
        verdict = "sell"
    else:
        verdict = "hold"

    return direction, confidence, verdict


# ---------------------------------------------------------------------------
# LLM rationale 생성 (reasons + risk_factors)
# ---------------------------------------------------------------------------

def _extract_json(text: str) -> dict:
    m = re.search(r"```(?:json)?\s*([\s\S]+?)\s*```", text)
    if m:
        return json.loads(m.group(1))
    m = re.search(r"\{[\s\S]+\}", text)
    if m:
        return json.loads(m.group(0))
    raise ValueError(f"JSON 블록 없음: {text[:200]}")


async def _generate_rationale(
    company: Optional[str],
    intent: str,
    direction: str,
    confidence: float,
    verdict: str,
    news_signal: dict,
    youtube_signal: dict,
) -> tuple[dict, list]:
    """LLM으로 판단 근거(reasons)와 리스크 요인(risk_factors) 생성."""
    pos_events = [e.get("event", "") for e in news_signal.get("positive_events", [])]
    neg_events = [e.get("event", "") for e in news_signal.get("negative_events", [])]
    bullish_kw = youtube_signal.get("bullish_keywords", [])
    bearish_kw = youtube_signal.get("bearish_keywords", [])
    news_kw = news_signal.get("keywords", [])

    human_msg = f"""종목: {company or "미지정"}
투자 의도: {intent}
판단 방향: {direction} | confidence: {confidence:.3f} | verdict: {verdict}

뉴스 긍정 이벤트: {pos_events}
뉴스 부정 이벤트: {neg_events}
뉴스 키워드: {news_kw}
유튜브 상승 키워드: {bullish_kw}
유튜브 하락 키워드: {bearish_kw}

아래 JSON 형식으로만 반환하세요. 투자 추천(매수/매도) 문구 사용 금지:
{{
    "reasons": {{
        "positive": ["긍정 근거 1", "긍정 근거 2", "긍정 근거 3"],
        "negative": ["부정 근거 1", "부정 근거 2"]
    }},
    "risk_factors": ["리스크 요인 1", "리스크 요인 2", "리스크 요인 3"]
}}"""

    settings = get_settings()
    llm = ChatOpenAI(
        api_key=settings.openai_api_key,
        model=settings.openai_model,
        temperature=0,
    )

    try:
        response = await llm.ainvoke([
            SystemMessage(content=(
                "당신은 투자 정보 분석 전문가입니다.\n"
                "주어진 신호 데이터를 바탕으로 판단 근거와 리스크 요인을 JSON으로 작성하세요.\n"
                "투자 추천 문구는 절대 사용하지 마세요. JSON 외 텍스트 금지."
            )),
            HumanMessage(content=human_msg),
        ])
        data = _extract_json(response.content.strip())
        reasons = data.get("reasons", {"positive": [], "negative": []})
        risk_factors = data.get("risk_factors", [])
        return reasons, risk_factors
    except Exception as e:
        await aemit(f"[InvestmentDecision] ✗ rationale LLM 실패: {e}")
        # fallback: 이벤트 리스트로 대체
        return (
            {"positive": pos_events[:3], "negative": neg_events[:3]},
            bearish_kw[:3] or ["정보 부족으로 리스크 평가 불가"],
        )


# ---------------------------------------------------------------------------
# 진입점
# ---------------------------------------------------------------------------

async def analyze_investment_decision(
    news_signal: Optional[dict],
    youtube_signal: Optional[dict],
    company: Optional[str] = None,
    intent: str = "전망 조회",
) -> dict:
    """투자 판단 결정 분석 진입점.

    Args:
        news_signal    : NewsSentimentMetrics dict
        youtube_signal : YouTubeSentimentMetrics dict
        company        : 종목명 (없으면 None)
        intent         : 투자 의도

    Returns:
        InvestmentDecision dict
    """
    ns = news_signal or {}
    ys = youtube_signal or {}

    await aemit(f"[InvestmentDecision] ▶ 시작 | company={company} | intent={intent}")

    # 입력 신호 부족 → 보수적 fallback
    has_news = bool(ns.get("positive_events") or ns.get("negative_events"))
    has_youtube = bool(ys.get("volume", 0) > 0)

    if not has_news and not has_youtube:
        await aemit("[InvestmentDecision] ⚠ 입력 신호 없음 → 보수적 fallback 반환")
        return _FALLBACK.copy()

    # --- Deterministic rule engine ---
    news_score = _compute_news_score(ns)
    sentiment_score = float(ys.get("sentiment_score", 0.0))

    await aemit(f"[InvestmentDecision]   뉴스 score={news_score:+.2f} | 감성 score={sentiment_score:+.2f}")

    direction, confidence, verdict = compute_direction_confidence_verdict(ns, ys)

    await aemit(f"[InvestmentDecision]   direction={direction} | confidence={confidence:.3f} | verdict={verdict}")

    # --- LLM rationale ---
    await aemit("[InvestmentDecision] → LLM rationale 생성 중...")
    reasons, risk_factors = await _generate_rationale(
        company, intent, direction, confidence, verdict, ns, ys
    )

    result = {
        "direction": direction,
        "confidence": confidence,
        "verdict": verdict,
        "reasons": reasons,
        "risk_factors": risk_factors,
    }

    # Pretty-print
    sep = "=" * 44
    await aemit(f"[InvestmentDecision] ◀ 완료")
    await aemit(f"[InvestmentDecision]   {sep}")
    await aemit(f"[InvestmentDecision]   direction  : {direction}")
    await aemit(f"[InvestmentDecision]   confidence : {confidence:.3f}")
    await aemit(f"[InvestmentDecision]   verdict    : {verdict}")
    await aemit(f"[InvestmentDecision]   positive   : {reasons.get('positive', [])}")
    await aemit(f"[InvestmentDecision]   negative   : {reasons.get('negative', [])}")
    await aemit(f"[InvestmentDecision]   risks      : {risk_factors}")
    await aemit(f"[InvestmentDecision]   {sep}")

    return result
