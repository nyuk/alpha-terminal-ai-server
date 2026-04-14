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


# ---------------------------------------------------------------------------
# 개별 소스 핸들러 (async, 실패 시 에러 문자열 반환)
# ---------------------------------------------------------------------------

async def _handle_news(keyword: str) -> str:
    """[Retrieval][뉴스] SERP API 뉴스 수집."""
    from app.domains.news_search.adapter.outbound.external.serp_news_search_adapter import SerpNewsSearchAdapter
    try:
        await aemit(f"[Retrieval][뉴스] ▶ SERP API 호출 | keyword={keyword}")
        loop = asyncio.get_event_loop()
        adapter = SerpNewsSearchAdapter(hl="ko", gl="kr")
        # SerpClient.get 은 동기 — event loop 블로킹 방지를 위해 executor 사용
        articles, total = await loop.run_in_executor(
            None, lambda: adapter.search(keyword=keyword, page=1, page_size=5)
        )
        if not articles:
            await aemit(f"[Retrieval][뉴스] 결과 없음")
            return ""
        lines = [f"=== 뉴스 ({total}건 중 {len(articles)}건 수집) ==="]
        for a in articles:
            lines.append(f"- [{a.source}] {a.title} ({a.published_at})")
            if a.snippet:
                lines.append(f"  {a.snippet}")
        await aemit(f"[Retrieval][뉴스] ◀ {len(articles)}건 수집 완료")
        return "\n".join(lines)
    except Exception:
        await aemit(f"[Retrieval][뉴스] ✗ 실패")
        traceback.print_exc()
        return "=== 뉴스 수집 실패 ==="


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
            return ""

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
        return "\n".join(lines)
    except Exception:
        await aemit(f"[Retrieval][YouTube] ✗ 수집 실패")
        traceback.print_exc()
        return "=== YouTube 수집 실패 ==="


async def _handle_stock(keyword: str) -> str:
    """[Retrieval][종목] 종목 기본 정보 수집 (향후 구현)."""
    await aemit(f"[Retrieval][종목] 향후 구현 예정 | keyword={keyword}")
    return "=== 종목 기본 정보: 향후 구현 예정 ==="


# ---------------------------------------------------------------------------
# SOURCE_REGISTRY
# 인터페이스: key → factory(keyword, query, company) → Coroutine[str]
# 새 소스 추가: 핸들러 함수 작성 후 아래에 한 줄만 추가하면 자동 병렬화 적용.
# ---------------------------------------------------------------------------

SourceFactory = Callable[[str, str, Optional[str]], Coroutine[Any, Any, str]]

SOURCE_REGISTRY: dict[str, SourceFactory] = {
    "뉴스":         lambda kw, q, c: _handle_news(kw),
    "YouTube 영상": lambda kw, q, c: _handle_youtube(kw, q, c),
    "종목":         lambda kw, q, c: _handle_stock(kw),
}


# ---------------------------------------------------------------------------
# 병렬 실행 헬퍼
# ---------------------------------------------------------------------------

async def _run_with_timeout(
    source_key: str,
    coro: Coroutine,
    timeout: float,
) -> str:
    """단일 소스 핸들러를 타임아웃과 함께 실행한다.

    타임아웃 또는 예외 발생 시 실패 메시지 문자열을 반환 (예외를 전파하지 않음).
    """
    try:
        return await asyncio.wait_for(coro, timeout=timeout)
    except asyncio.TimeoutError:
        await aemit(f"[Retrieval][{source_key}] ✗ 타임아웃 ({timeout}s 초과)")
        return f"=== {source_key} 수집 타임아웃 ({timeout}s) ==="
    except Exception:
        await aemit(f"[Retrieval][{source_key}] ✗ 예외 발생")
        traceback.print_exc()
        return f"=== {source_key} 수집 실패 ==="


def _merge_results(keys_in_order: List[str], results: List[str]) -> str:
    """required_data 순서대로 수집 결과를 병합한다."""
    sections = [r for r in results if r]
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

    results: List[str] = await asyncio.gather(
        *[_run_with_timeout(key, coro, HANDLER_TIMEOUT)
          for key, coro in zip(active_keys, coroutines)]
    )

    elapsed = time.perf_counter() - t_start
    await aemit(f"[Retrieval] ⚡ 병렬 실행 완료 | 소요={elapsed:.1f}s")

    # 개별 소스 결과 로그
    for key, result in zip(active_keys, results):
        status = "✓" if result and "실패" not in result and "타임아웃" not in result else "✗"
        await aemit(f"[Retrieval]   {status} [{key}] {len(result)}자")

    # required_data 순서대로 병합
    retrieved_data = _merge_results(active_keys, list(results))
    await aemit(f"[Retrieval] ◀ 완료 | 총 {len(retrieved_data)}자")

    return {"retrieved_data": retrieved_data}
