"""투자 판단 워크플로우용 뉴스 본문 수집 서비스.

흐름:
    SERP API → 뉴스 목록 → ArticleContentFetcher 본문 추출
    → MySQL (investment_news) + PG (investment_news_contents) 저장
    → retrieval_data 포맷 텍스트 반환

부분 실패 정책:
    개별 뉴스 본문 수집 실패 시 해당 뉴스만 content=None 으로 기록하고 나머지 계속 진행.
    DB 저장 실패 시 traceback 출력 후 수집 결과 텍스트는 그대로 반환.
"""
import asyncio
import traceback
from hashlib import sha256
from typing import Optional

from app.domains.investment.adapter.outbound.agent.log_context import aemit
from app.domains.news_search.adapter.outbound.external.serp_news_search_adapter import SerpNewsSearchAdapter
from app.infrastructure.external.article_content_fetcher import ArticleContentFetcher

DEFAULT_KEYWORD = "방산"
CONTENT_PREVIEW_CHARS = 800  # retrieval_data 에 포함할 본문 미리보기 최대 글자 수
NEWS_PAGE_SIZE = 5


def _save_to_db(articles_data: list) -> dict:
    """MySQL + PostgreSQL 저장 (동기 — executor 에서 호출).

    Returns:
        {"success": bool, "count": int, "error": str | None}
    """
    from app.domains.news_search.infrastructure.orm.investment_news_orm import InvestmentNewsORM
    from app.domains.news_search.infrastructure.orm.investment_news_content_orm import InvestmentNewsContentORM
    from app.infrastructure.database.session import SessionLocal
    from app.infrastructure.database.pg_session import PgSessionLocal

    mysql_db = SessionLocal()
    pg_db = PgSessionLocal()
    success_count = 0
    try:
        for data in articles_data:
            # 기사 단위 트랜잭션 — 실패 시 해당 건만 rollback하고 다음 건 계속 진행
            try:
                link_hash = sha256(data["link"].encode()).hexdigest()
                existing = (
                    mysql_db.query(InvestmentNewsORM)
                    .filter(InvestmentNewsORM.link_hash == link_hash)
                    .first()
                )
                if existing:
                    article_id = existing.id
                    print(f"[InvestmentNews][MySQL] 중복 건너뜀: {data['title'][:40]}")
                else:
                    orm = InvestmentNewsORM(
                        company=data.get("company"),
                        keyword=data["keyword"],
                        title=data["title"],
                        source=data.get("source", ""),
                        link=data["link"],
                        link_hash=link_hash,
                        snippet=data.get("snippet"),
                        published_at=data.get("published_at"),
                    )
                    mysql_db.add(orm)
                    mysql_db.flush()
                    article_id = orm.id
                    print(f"[InvestmentNews][MySQL] 저장: id={article_id} | {data['title'][:40]}")

                # --- PostgreSQL: 본문 JSONB ---
                if data.get("content") and article_id:
                    try:
                        content_orm = InvestmentNewsContentORM(
                            article_id=article_id,
                            raw_data={
                                "title": data["title"],
                                "source": data.get("source", ""),
                                "link": data["link"],
                                "snippet": data.get("snippet"),
                                "published_at": data.get("published_at"),
                                "content": data["content"],
                            },
                        )
                        pg_db.add(content_orm)
                        print(f"[InvestmentNews][PG] 본문 저장: article_id={article_id}")
                    except Exception:
                        print(f"[InvestmentNews][PG] ✗ 본문 저장 실패: article_id={article_id}")
                        traceback.print_exc()

                # 기사 단위 commit — flush 실패 시 이 줄에 도달하지 않음
                mysql_db.commit()
                pg_db.commit()
                success_count += 1

            except Exception:
                # 이 건만 rollback — 세션을 깨끗하게 초기화하여 다음 건 처리 가능
                mysql_db.rollback()
                pg_db.rollback()
                print(f"[InvestmentNews][MySQL] ✗ 저장 실패: {data.get('title', '')[:40]}")
                traceback.print_exc()

        print(f"[InvestmentNews] DB commit 완료 | {success_count}/{len(articles_data)}건")
        return {"success": True, "count": success_count, "error": None}

    except Exception as e:
        mysql_db.rollback()
        pg_db.rollback()
        print("[InvestmentNews] ✗ DB 트랜잭션 실패 → rollback")
        traceback.print_exc()
        return {"success": False, "count": 0, "error": str(e)}
    finally:
        mysql_db.close()
        pg_db.close()


async def fetch_and_store_investment_news(
    keyword: str,
    company: Optional[str] = None,
    page_size: int = NEWS_PAGE_SIZE,
) -> tuple[str, dict]:
    """투자 판단 워크플로우용 뉴스 본문 수집 진입점.

    Args:
        keyword: 검색 키워드 (company 또는 사용자 쿼리). 비어 있으면 DEFAULT_KEYWORD 사용.
        company: 파싱된 종목명 (DB 저장용, 없으면 None).
        page_size: SERP API 검색 결과 수 (기본 5).

    Returns:
        retrieval_data 에 적재할 포맷 텍스트.
    """
    effective_keyword = keyword.strip() if keyword else DEFAULT_KEYWORD
    await aemit(f"[InvestmentNews] ▶ 시작 | keyword={effective_keyword} company={company}")

    # 1. SERP API 뉴스 목록 검색
    loop = asyncio.get_event_loop()
    try:
        adapter = SerpNewsSearchAdapter(hl="ko", gl="kr")
        articles, total = await loop.run_in_executor(
            None,
            lambda: adapter.search(keyword=effective_keyword, page=1, page_size=page_size),
        )
    except Exception:
        await aemit("[InvestmentNews] ✗ SERP 검색 실패")
        traceback.print_exc()
        return "=== 투자 뉴스 수집 실패 ===", {}

    if not articles:
        await aemit("[InvestmentNews] ⚠ 검색 결과 없음")
        return "=== 투자 뉴스: 결과 없음 ===", {}

    await aemit(f"[InvestmentNews]   {total}건 중 {len(articles)}건 → 본문 추출 시작")

    # 2. 각 기사 본문 추출 (부분 실패 허용)
    fetcher = ArticleContentFetcher()
    articles_data = []
    lines = [f"=== 투자 뉴스 (keyword={effective_keyword}, {len(articles)}건) ==="]

    for article in articles:
        if not article.link:
            continue

        content: Optional[str] = None
        try:
            url = article.link
            content = await loop.run_in_executor(None, lambda u=url: fetcher.fetch(u))
            char_count = len(content) if content else 0
            await aemit(f"[InvestmentNews]   ✓ 본문 {char_count}자 | {article.title[:40]}")
        except Exception:
            await aemit(f"[InvestmentNews]   ✗ 본문 수집 실패 | {article.title[:40]}")
            traceback.print_exc()

        articles_data.append({
            "company": company,
            "keyword": effective_keyword,
            "title": article.title,
            "source": article.source,
            "link": article.link,
            "snippet": article.snippet,
            "published_at": article.published_at,
            "content": content,
        })

        # retrieval_data 포맷 구성
        lines.append(f"\n[{article.source}] {article.title} ({article.published_at})")
        if article.snippet:
            lines.append(f"요약: {article.snippet}")
        if content:
            preview = content[:CONTENT_PREVIEW_CHARS].replace("\n", " ")
            lines.append(f"본문: {preview}{'...' if len(content) > CONTENT_PREVIEW_CHARS else ''}")

    # 3. DB 저장 (부분 실패 허용)
    await aemit(f"[InvestmentNews] → DB 저장 | {len(articles_data)}건")
    try:
        await loop.run_in_executor(None, lambda: _save_to_db(articles_data))
    except Exception:
        await aemit("[InvestmentNews] ✗ DB 저장 실패 (수집 결과는 유지)")
        traceback.print_exc()

    # 4. 뉴스 투자 심리 지표 산출
    news_metrics: dict = {}
    try:
        from app.domains.investment.adapter.outbound.agent.sentiment_analyzer import analyze_news_articles
        await aemit(f"[InvestmentNews] → 뉴스 심리 지표 산출 시작")
        news_metrics = await analyze_news_articles(articles_data)
        lines.append(f"\n=== 뉴스 투자 심리 지표 ===")
        for ev in news_metrics.get("positive_events", []):
            lines.append(f"[긍정] {ev['event']} (영향: {ev.get('impact', '-')})")
        for ev in news_metrics.get("negative_events", []):
            lines.append(f"[부정] {ev['event']} (영향: {ev.get('impact', '-')})")
        kw = news_metrics.get("keywords", [])
        if kw:
            lines.append(f"주요 키워드: {', '.join(kw)}")
    except Exception:
        await aemit("[InvestmentNews] ✗ 뉴스 심리 지표 산출 실패 (수집 결과는 유지)")
        traceback.print_exc()

    result_text = "\n".join(lines)
    await aemit(f"[InvestmentNews] ◀ 완료 | {len(articles_data)}건 / 총 {len(result_text)}자")
    return result_text, news_metrics
