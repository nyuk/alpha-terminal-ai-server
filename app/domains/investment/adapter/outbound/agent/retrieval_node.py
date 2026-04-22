"""Retrieval Agent 노드 — parsed_query.required_data 기반으로 데이터 소스를 병렬 호출한다.

병렬화 전략:
    asyncio.gather + asyncio.wait_for 로 SOURCE_REGISTRY 핸들러를 동시 실행.
    전체 소요 시간 ≈ max(단일 소스 시간) + 소규모 오버헤드.

SOURCE_REGISTRY 인터페이스:
    key   : required_data 식별자 (str)
    value : async handler factory — (keyword, query, company) → Coroutine → str
    새 소스 추가 시 SOURCE_REGISTRY 에 key/factory 하나만 추가하면 자동 병렬화 적용.

부분 실패 정책:
    asyncio.wait_for 타임아웃(30s) 초과 또는 예외 발생 시
    해당 소스만 실패 메시지로 대체하고 나머지는 정상 반영.

결과 순서:
    required_data 배열 순서대로 sections 를 병합하여 일관성 유지.
"""
import asyncio
import time
import traceback
from typing import Callable, Coroutine, List, Optional, Any

from app.domains.investment.adapter.outbound.agent.investment_agent_state import InvestmentAgentState
from app.domains.investment.adapter.outbound.agent.log_context import aemit
from app.infrastructure.config.settings import get_settings

HANDLER_TIMEOUT = 30  # 소스별 최대 실행 시간 (초)

SourceResult = tuple[str, Optional[dict]]   # (retrieval_text, signal_dict)
SourceFactory = Callable[[str, str, Optional[str]], Coroutine[Any, Any, SourceResult]]


# ---------------------------------------------------------------------------
# 개별 소스 핸들러 (async, 실패 시 에러 문자열 반환)
# ---------------------------------------------------------------------------

async def _handle_news(keyword: str, company: Optional[str] = None) -> SourceResult:
    """[Retrieval][뉴스] SERP API 뉴스 검색 + ArticleContentFetcher 본문 수집 + DB 저장."""
    from app.domains.news_search.adapter.outbound.external.investment_news_source import (
        fetch_and_store_investment_news,
    )
    return await fetch_and_store_investment_news(keyword=keyword, company=company)


async def _handle_youtube(keyword: str, query: str, company: Optional[str]) -> str:
    """[Retrieval][YouTube] YouTube API 영상 수집 + MySQL/PG DB 저장."""
    from app.domains.youtube.adapter.outbound.external.youtube_api_adapter import YouTubeApiAdapter
    from app.domains.investment.infrastructure.repository.investment_youtube_repository import save_youtube_collection
    try:
        keywords = [keyword]
        await aemit(f"[Retrieval][YouTube] ▶ YouTube API 호출 | keywords={keywords}")
        settings = get_settings()
        adapter = YouTubeApiAdapter(api_key=settings.youtube_api_key)
        videos = await adapter.collect_from_channels(keywords=keywords, days=7, max_per_channel=3)

        if not videos:
            await aemit(f"[Retrieval][YouTube] 결과 없음")
            save_youtube_collection(query=query, company=company, videos=[], comments_by_video={})
            return "", None

        await aemit(f"[Retrieval][YouTube] ◀ {len(videos)}건 수집 → 댓글 수집 시작")
        comments_by_video: dict = {}
        for video in videos:
            try:
                comments = await adapter.fetch_comments(video_id=video.video_id, max_results=10)
                comments_by_video[video.video_id] = comments
                await aemit(f"[Retrieval][YouTube]   댓글 {len(comments)}건 | {video.video_id}")
            except Exception:
                await aemit(f"[Retrieval][YouTube] ✗ 댓글 수집 실패: {video.video_id}")
                traceback.print_exc()
                comments_by_video[video.video_id] = []

        await aemit(f"[Retrieval][YouTube] → DB 저장 시작")
        try:
            save_youtube_collection(
                query=query, company=company,
                videos=videos, comments_by_video=comments_by_video,
            )
        except Exception:
            await aemit(f"[Retrieval][YouTube] ✗ DB 저장 실패 (수집 결과는 유지)")
            traceback.print_exc()

        lines = [f"=== YouTube 영상 ({len(videos)}건 수집) ==="]
        for v in videos:
            lines.append(f"- [{v.channel_name}] {v.title} ({v.published_at})")
            lines.append(f"  {v.video_url}")
        total_comments = sum(len(c) for c in comments_by_video.values())
        await aemit(f"[Retrieval][YouTube] ◀ 완료 | {len(videos)}건 영상 / {total_comments}건 댓글")

        # YouTube 투자 심리 지표 산출
        youtube_metrics: dict = {}
        try:
            from app.domains.investment.adapter.outbound.agent.sentiment_analyzer import analyze_youtube_comments
            await aemit(f"[Retrieval][YouTube] → 투자 심리 지표 산출 시작")
            all_texts = [c.text for cs in comments_by_video.values() for c in cs]
            youtube_metrics = await analyze_youtube_comments(all_texts, company)
            sd = youtube_metrics["sentiment_distribution"]
            lines.append(f"\n=== YouTube 투자 심리 지표 ===")
            lines.append(f"감성 분포: 긍정 {sd['positive']:.0%} / 중립 {sd['neutral']:.0%} / 부정 {sd['negative']:.0%}")
            lines.append(f"감성 점수: {youtube_metrics['sentiment_score']:+.2f}")
            lines.append(f"상승 키워드: {', '.join(youtube_metrics['bullish_keywords'])}")
            lines.append(f"하락 키워드: {', '.join(youtube_metrics['bearish_keywords'])}")
            lines.append(f"주요 토픽: {', '.join(youtube_metrics['topics'])}")
            lines.append(f"분석 댓글 수: {youtube_metrics['volume']}건")
        except Exception:
            await aemit(f"[Retrieval][YouTube] ✗ 심리 지표 산출 실패 (영상 수집 결과는 유지)")
            traceback.print_exc()

        return "\n".join(lines), youtube_metrics or None
    except Exception:
        await aemit(f"[Retrieval][YouTube] ✗ 수집 실패")
        traceback.print_exc()
        return "=== YouTube 수집 실패 ===", None


async def _handle_dashboard_analysis(keyword: str, company: Optional[str] = None) -> SourceResult:
    """[Retrieval][대시보드 분석] analysis_logs 테이블에서 최근 48시간 내 종목 분석 결과를 조회한다."""
    from datetime import datetime, timedelta
    from app.domains.stock.infrastructure.orm.stock_orm import StockORM
    from app.domains.pipeline.infrastructure.orm.analysis_log_orm import AnalysisLogORM
    from app.infrastructure.database.session import SessionLocal

    search_name = company or keyword
    await aemit(f"[Retrieval][대시보드 분석] ▶ 시작 | keyword={search_name}")

    loop = asyncio.get_event_loop()

    def _query_logs():
        db = SessionLocal()
        try:
            # company명으로 symbol 조회
            stock_orm = db.query(StockORM).filter(StockORM.name == search_name).first()
            if not stock_orm:
                stock_orm = db.query(StockORM).filter(StockORM.name.like(f"%{search_name}%")).first()

            if not stock_orm:
                return None, search_name

            cutoff = datetime.now() - timedelta(hours=48)
            logs = (
                db.query(AnalysisLogORM)
                .filter(
                    AnalysisLogORM.symbol == stock_orm.symbol,
                    AnalysisLogORM.analyzed_at >= cutoff,
                )
                .order_by(AnalysisLogORM.analyzed_at.desc())
                .limit(5)
                .all()
            )
            return logs, stock_orm.name
        finally:
            db.close()

    try:
        logs, stock_name = await loop.run_in_executor(None, _query_logs)
    except Exception:
        await aemit(f"[Retrieval][대시보드 분석] ✗ DB 조회 실패")
        traceback.print_exc()
        return "", None

    if logs is None:
        await aemit(f"[Retrieval][대시보드 분석] ⚠ 종목 미등록: {search_name}")
        return "", None

    if not logs:
        await aemit(f"[Retrieval][대시보드 분석] ⚠ 최근 48h 분석 기록 없음: {stock_name}")
        return "", None

    lines = [f"=== 대시보드 AI 분석 기록: {stock_name} (최근 48시간, {len(logs)}건) ==="]
    for log in logs:
        lines.append(f"\n[{log.analyzed_at.strftime('%Y-%m-%d %H:%M')}] [{log.source_type}] {log.source_name or ''}")
        lines.append(f"감성: {log.sentiment} (점수={log.sentiment_score:.2f}, 신뢰도={log.confidence:.2f})")
        lines.append(f"태그: {', '.join(log.tags) if log.tags else '없음'}")
        lines.append(f"요약: {log.summary}")

    result_text = "\n".join(lines)
    await aemit(f"[Retrieval][대시보드 분석] ◀ 완료 | {len(logs)}건 / {len(result_text)}자")
    return result_text, None


async def _handle_stock(keyword: str, company: Optional[str] = None) -> SourceResult:
    """[Retrieval][종목] DART 재무제표 + 공시 수집.

    흐름:
        stocks DB에서 종목명으로 corp_code 조회
        → DartReportCollectorAdapter(재무제표) + DartCollectorAdapter(공시) 병렬 수집
    """
    from app.domains.stock.infrastructure.orm.stock_orm import StockORM
    from app.infrastructure.database.session import SessionLocal
    from app.domains.stock_collector.adapter.outbound.external.dart_report_collector_adapter import DartReportCollectorAdapter
    from app.domains.stock_collector.adapter.outbound.external.dart_collector_adapter import DartCollectorAdapter

    search_name = company or keyword
    await aemit(f"[Retrieval][종목] ▶ 시작 | keyword={search_name}")

    loop = asyncio.get_event_loop()

    def _lookup_stock():
        db = SessionLocal()
        try:
            orm = db.query(StockORM).filter(StockORM.name == search_name).first()
            if not orm:
                orm = db.query(StockORM).filter(StockORM.name.like(f"%{search_name}%")).first()
            return orm
        finally:
            db.close()

    stock_orm = await loop.run_in_executor(None, _lookup_stock)

    if not stock_orm:
        await aemit(f"[Retrieval][종목] ⚠ 종목 미등록: {search_name}")
        return f"=== 종목 정보 없음: {search_name} (DB 미등록) ===", None

    symbol = stock_orm.symbol
    stock_name = stock_orm.name
    corp_code = stock_orm.corp_code
    await aemit(f"[Retrieval][종목] ◀ 종목 확인: {stock_name}({symbol}) corp_code={corp_code}")

    def _collect_financial():
        return DartReportCollectorAdapter().collect(symbol=symbol, stock_name=stock_name, corp_code=corp_code)

    def _collect_disclosures():
        return DartCollectorAdapter().collect(symbol=symbol, stock_name=stock_name, corp_code=corp_code)

    await aemit(f"[Retrieval][종목] → DART 재무제표 + 공시 병렬 수집 시작")
    financial_articles, disclosure_articles = await asyncio.gather(
        loop.run_in_executor(None, _collect_financial),
        loop.run_in_executor(None, _collect_disclosures),
    )

    lines = [f"=== 종목 정보: {stock_name}({symbol}) ==="]

    if financial_articles:
        for a in financial_articles:
            lines.append(f"\n{a.body_text}")
        await aemit(f"[Retrieval][종목] ✓ 재무제표 {len(financial_articles)}건")
    else:
        lines.append("\n[재무제표] 데이터 없음")
        await aemit(f"[Retrieval][종목] ⚠ 재무제표 없음")

    if disclosure_articles:
        lines.append(f"\n[최근 공시 {len(disclosure_articles)}건]")
        for a in disclosure_articles:
            lines.append(f"- {a.title} ({a.published_at})")
        await aemit(f"[Retrieval][종목] ✓ 공시 {len(disclosure_articles)}건")
    else:
        lines.append("\n[최근 공시] 없음")
        await aemit(f"[Retrieval][종목] ⚠ 공시 없음")

    result_text = "\n".join(lines)
    await aemit(f"[Retrieval][종목] ◀ 완료 | {len(result_text)}자")
    return result_text, None


# ---------------------------------------------------------------------------
# SOURCE_REGISTRY
# 인터페이스: key → factory(keyword, query, company) → Coroutine[str]
# 새 소스 추가: 핸들러 함수 작성 후 아래에 한 줄만 추가하면 자동 병렬화 적용.
# ---------------------------------------------------------------------------

SOURCE_REGISTRY: dict[str, SourceFactory] = {
    "뉴스":         lambda kw, q, c: _handle_news(kw, c),
    "YouTube 영상": lambda kw, q, c: _handle_youtube(kw, q, c),
    "종목":         lambda kw, q, c: _handle_stock(kw, c),
    "대시보드 분석": lambda kw, q, c: _handle_dashboard_analysis(kw, c),
}


# ---------------------------------------------------------------------------
# 병렬 실행 헬퍼
# ---------------------------------------------------------------------------

async def _run_with_timeout(
    source_key: str,
    coro: Coroutine,
    timeout: float,
) -> SourceResult:
    """단일 소스 핸들러를 타임아웃과 함께 실행한다.

    타임아웃 또는 예외 발생 시 실패 메시지를 반환 (예외를 전파하지 않음).
    """
    try:
        return await asyncio.wait_for(coro, timeout=timeout)
    except asyncio.TimeoutError:
        await aemit(f"[Retrieval][{source_key}] ✗ 타임아웃 ({timeout}s 초과)")
        return f"=== {source_key} 수집 타임아웃 ({timeout}s) ===", None
    except Exception:
        await aemit(f"[Retrieval][{source_key}] ✗ 예외 발생")
        traceback.print_exc()
        return f"=== {source_key} 수집 실패 ===", None


def _merge_results(keys_in_order: List[str], texts: List[str]) -> str:
    """required_data 순서대로 수집 결과를 병합한다."""
    sections = [r for r in texts if r]
    return "\n\n".join(sections) if sections else "수집된 데이터 없음"


# ---------------------------------------------------------------------------
# Retrieval 노드 진입점
# ---------------------------------------------------------------------------

async def retrieval_node(state: InvestmentAgentState) -> dict:
    """Retrieval 노드: SOURCE_REGISTRY 핸들러를 asyncio.gather 로 병렬 실행한다."""
    query = state["query"]
    parsed_query = state.get("parsed_query") or {}
    required_data: List[str] = parsed_query.get("required_data", [])
    company: Optional[str] = parsed_query.get("company")

    keyword = company if company else query

    # SOURCE_REGISTRY 에 등록된 키만 처리 (required_data 순서 유지)
    active_keys = [k for k in required_data if k in SOURCE_REGISTRY]
    skipped_keys = [k for k in required_data if k not in SOURCE_REGISTRY]

    await aemit(f"[Retrieval] ▶ 시작 | keyword={keyword}")
    await aemit(f"[Retrieval]   수집 소스: {active_keys}" + (f" | 미등록: {skipped_keys}" if skipped_keys else ""))

    if not active_keys:
        await aemit(f"[Retrieval] ⚠ 실행할 소스 없음")
        return {"retrieved_data": "수집된 데이터 없음"}

    # 코루틴 생성 (required_data 순서대로)
    coroutines = [
        SOURCE_REGISTRY[key](keyword, query, company)
        for key in active_keys
    ]

    # 병렬 실행 + 타임아웃 래핑
    await aemit(f"[Retrieval] ⚡ {len(active_keys)}개 소스 병렬 실행 (timeout={HANDLER_TIMEOUT}s)")
    t_start = time.perf_counter()

    raw_results: List[SourceResult] = await asyncio.gather(
        *[_run_with_timeout(key, coro, HANDLER_TIMEOUT)
          for key, coro in zip(active_keys, coroutines)]
    )

    elapsed = time.perf_counter() - t_start
    await aemit(f"[Retrieval] ⚡ 병렬 실행 완료 | 소요={elapsed:.1f}s")

    # 텍스트·신호 분리
    texts: List[str] = [r[0] for r in raw_results]
    signals: dict[str, Optional[dict]] = {
        key: r[1] for key, r in zip(active_keys, raw_results)
    }

    # 개별 소스 결과 로그
    for key, text in zip(active_keys, texts):
        status = "✓" if text and "실패" not in text and "타임아웃" not in text else "✗"
        await aemit(f"[Retrieval]   {status} [{key}] {len(text)}자")

    # required_data 순서대로 병합
    retrieved_data = _merge_results(active_keys, texts)
    await aemit(f"[Retrieval] ◀ 완료 | 총 {len(retrieved_data)}자")

    return {
        "retrieved_data": retrieved_data,
        "news_signal": signals.get("뉴스"),
        "youtube_signal": signals.get("YouTube 영상"),
    }
