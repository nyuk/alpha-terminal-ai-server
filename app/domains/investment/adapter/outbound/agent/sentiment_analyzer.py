"""투자 심리 지표 산출 모듈.

YouTube 댓글과 뉴스 기사를 LLM으로 분석하여 구조화된 투자 심리 지표를 반환한다.

YouTube 지표:
    {
        "sentiment_distribution": {"positive": float, "neutral": float, "negative": float},
        "sentiment_score": float,   # -1(매우부정) ~ +1(매우긍정)
        "bullish_keywords": [...],  # 긍정 그룹 키워드 TOP 5
        "bearish_keywords": [...],  # 부정 그룹 키워드 TOP 5
        "topics": [...],            # 전체 주요 토픽 TOP 5
        "volume": int               # 분석 기반 댓글 수
    }

뉴스 지표:
    {
        "positive_events": [{"event": str, "impact": "high|medium|low"}],
        "negative_events": [{"event": str, "impact": "high|medium|low"}],
        "keywords": [...]           # 핵심 투자 키워드 TOP 10
    }
"""
import json
import re
from typing import Optional

from langchain_core.messages import HumanMessage, SystemMessage
from langchain_openai import ChatOpenAI

from app.domains.investment.adapter.outbound.agent.log_context import aemit
from app.infrastructure.config.settings import get_settings

MAX_COMMENTS = 200           # LLM에 전달할 최대 댓글 수
COMMENT_MAX_CHARS = 80       # 댓글당 최대 글자 수 (토큰 절약)
NEWS_CONTENT_PREVIEW = 300   # 뉴스 본문 미리보기 최대 글자 수


# ---------------------------------------------------------------------------
# 빈 지표 fallback
# ---------------------------------------------------------------------------

def _empty_youtube_metrics(volume: int = 0) -> dict:
    return {
        "sentiment_distribution": {"positive": 0.0, "neutral": 1.0, "negative": 0.0},
        "sentiment_score": 0.0,
        "bullish_keywords": [],
        "bearish_keywords": [],
        "topics": [],
        "volume": volume,
    }


def _empty_news_metrics() -> dict:
    return {
        "positive_events": [],
        "negative_events": [],
        "keywords": [],
    }


# ---------------------------------------------------------------------------
# JSON 파싱 헬퍼
# ---------------------------------------------------------------------------

def _extract_json(text: str) -> dict:
    match = re.search(r"```(?:json)?\s*([\s\S]+?)\s*```", text)
    if match:
        return json.loads(match.group(1))
    match = re.search(r"\{[\s\S]+\}", text)
    if match:
        return json.loads(match.group(0))
    raise ValueError(f"JSON 블록 없음: {text[:200]}")


# ---------------------------------------------------------------------------
# YouTube 댓글 감성 분석
# ---------------------------------------------------------------------------

async def analyze_youtube_comments(
    comments: list[str],
    company: Optional[str] = None,
) -> dict:
    """유튜브 댓글 리스트 → YouTube 투자 심리 지표.

    Args:
        comments: 댓글 텍스트 리스트 (50~250건 권장)
        company: 종목명 (프롬프트 컨텍스트용, 없으면 None)

    Returns:
        YouTubeSentimentMetrics dict. 실패 시 빈 지표 반환.
    """
    volume = len(comments)

    if not comments:
        await aemit("[SentimentAnalyzer][YouTube] ⚠ 댓글 없음 → 빈 지표 반환")
        return _empty_youtube_metrics(0)

    sample = comments[:MAX_COMMENTS]
    formatted = "\n".join(
        f"{i + 1}. {c[:COMMENT_MAX_CHARS]}" for i, c in enumerate(sample)
    )

    await aemit(
        f"[SentimentAnalyzer][YouTube] ▶ 분석 시작 | "
        f"전체 {volume}건 → 샘플 {len(sample)}건 | company={company}"
    )

    settings = get_settings()
    llm = ChatOpenAI(
        api_key=settings.openai_api_key,
        model=settings.openai_model,
        temperature=0,
    )

    system_msg = (
        "당신은 주식 투자 심리 분석 전문가입니다.\n"
        "유튜브 댓글들을 분석하여 투자 심리 지표를 JSON으로 반환하세요.\n"
        "JSON 외 다른 텍스트를 포함하지 마세요."
    )

    human_msg = f"""종목: {company or "미지정"}
총 댓글 수: {volume}건 (아래 {len(sample)}건 샘플 분석)

댓글 목록:
{formatted}

아래 형식의 JSON만 반환하세요:
{{
    "sentiment_distribution": {{
        "positive": 0.40,
        "neutral": 0.35,
        "negative": 0.25
    }},
    "sentiment_score": 0.15,
    "bullish_keywords": ["매수", "상승", "호재", "목표가", "수주"],
    "bearish_keywords": ["하락", "리스크", "우려", "매도", "손실"],
    "topics": ["방산", "수출", "실적", "수주", "밸류에이션"],
    "volume": {volume}
}}

주의:
- sentiment_distribution 세 값의 합계는 반드시 1.0
- sentiment_score: 긍정·부정 비율 기반 -1(매우부정) ~ +1(매우긍정) 연속값
- bullish_keywords: 긍정 댓글에서 자주 등장하는 한국어 투자 키워드 TOP 5
- bearish_keywords: 부정 댓글에서 자주 등장하는 한국어 투자 키워드 TOP 5
- topics: 전체 댓글의 주요 투자 관련 토픽 TOP 5
- volume: 반드시 {volume} (전체 댓글 수)"""

    try:
        response = await llm.ainvoke([
            SystemMessage(content=system_msg),
            HumanMessage(content=human_msg),
        ])
        metrics = _extract_json(response.content.strip())
        metrics["volume"] = volume  # 전체 댓글 수 보정

        sd = metrics.get("sentiment_distribution", {})
        await aemit(f"[SentimentAnalyzer][YouTube] ◀ 분석 완료")
        await aemit(
            f"[SentimentAnalyzer][YouTube]   "
            f"감성점수={metrics.get('sentiment_score', 0):+.2f} | "
            f"긍정={sd.get('positive', 0):.0%} / "
            f"중립={sd.get('neutral', 0):.0%} / "
            f"부정={sd.get('negative', 0):.0%}"
        )
        await aemit(f"[SentimentAnalyzer][YouTube]   상승키워드={metrics.get('bullish_keywords', [])}")
        await aemit(f"[SentimentAnalyzer][YouTube]   하락키워드={metrics.get('bearish_keywords', [])}")
        await aemit(f"[SentimentAnalyzer][YouTube]   토픽={metrics.get('topics', [])}")
        await aemit(f"[SentimentAnalyzer][YouTube]   분석댓글={metrics['volume']}건")

        return metrics

    except Exception as e:
        await aemit(f"[SentimentAnalyzer][YouTube] ✗ 분석 실패: {e}")
        return _empty_youtube_metrics(volume)


# ---------------------------------------------------------------------------
# 뉴스 기사 감성 분석
# ---------------------------------------------------------------------------

async def analyze_news_articles(articles: list[dict]) -> dict:
    """뉴스 기사 리스트 → 뉴스 투자 심리 지표.

    Args:
        articles: 기사 dict 리스트 (title, source, snippet, published_at, content 키 포함)

    Returns:
        NewsSentimentMetrics dict. 실패 시 빈 지표 반환.
    """
    if not articles:
        await aemit("[SentimentAnalyzer][뉴스] ⚠ 기사 없음 → 빈 지표 반환")
        return _empty_news_metrics()

    await aemit(f"[SentimentAnalyzer][뉴스] ▶ 분석 시작 | {len(articles)}건")

    parts = []
    for i, a in enumerate(articles):
        content_preview = (a.get("content") or "")[:NEWS_CONTENT_PREVIEW].replace("\n", " ")
        parts.append(
            f"[기사 {i + 1}] {a.get('title', '')} ({a.get('source', '')} / {a.get('published_at', '')})\n"
            f"  요약: {a.get('snippet', '')}\n"
            f"  본문: {content_preview}"
        )
    formatted = "\n\n".join(parts)

    settings = get_settings()
    llm = ChatOpenAI(
        api_key=settings.openai_api_key,
        model=settings.openai_model,
        temperature=0,
    )

    system_msg = (
        "당신은 주식 투자 뉴스 분석 전문가입니다.\n"
        "뉴스 기사들을 분석하여 투자 관련 이벤트와 키워드를 JSON으로 반환하세요.\n"
        "JSON 외 다른 텍스트를 포함하지 마세요."
    )

    human_msg = f"""아래 뉴스 기사들을 분석하세요:

{formatted}

아래 형식의 JSON만 반환하세요:
{{
    "positive_events": [
        {{"event": "방산 수출 수주 증가", "impact": "high"}},
        {{"event": "실적 개선 기대감 상승", "impact": "medium"}}
    ],
    "negative_events": [
        {{"event": "원자재 가격 상승", "impact": "medium"}},
        {{"event": "경쟁사 신제품 출시", "impact": "low"}}
    ],
    "keywords": ["방산", "수출", "수주", "실적", "원자재", "경쟁", "밸류에이션", "목표가"]
}}

주의:
- positive_events: 주가에 긍정적 영향을 줄 이벤트 (최대 5개)
- negative_events: 주가에 부정적 영향을 줄 이벤트 (최대 5개)
- impact: "high" | "medium" | "low" 중 하나
- keywords: 전체 뉴스의 핵심 투자 관련 키워드 TOP 10"""

    try:
        response = await llm.ainvoke([
            SystemMessage(content=system_msg),
            HumanMessage(content=human_msg),
        ])
        metrics = _extract_json(response.content.strip())

        await aemit(f"[SentimentAnalyzer][뉴스] ◀ 분석 완료")
        await aemit(
            f"[SentimentAnalyzer][뉴스]   "
            f"긍정이벤트={[e['event'] for e in metrics.get('positive_events', [])]}"
        )
        await aemit(
            f"[SentimentAnalyzer][뉴스]   "
            f"부정이벤트={[e['event'] for e in metrics.get('negative_events', [])]}"
        )
        await aemit(f"[SentimentAnalyzer][뉴스]   키워드={metrics.get('keywords', [])}")

        return metrics

    except Exception as e:
        await aemit(f"[SentimentAnalyzer][뉴스] ✗ 분석 실패: {e}")
        return _empty_news_metrics()
