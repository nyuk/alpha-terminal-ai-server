"""Create a reviewed local StockBrief handoff for Trading Ops.

This is a one-shot local projection from StockBrief's reviewed analysis logs
and watchlist rows into the Trading Ops stock research handoff contract. It
intentionally excludes source URLs, raw article bodies, account ids, hashes,
and recommendation fields.
"""

from __future__ import annotations

import argparse
import json
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from sqlalchemy import func

from app.domains.pipeline.infrastructure.orm.analysis_log_orm import AnalysisLogORM
from app.domains.watchlist.infrastructure.orm.watchlist_item_orm import WatchlistItemORM
from app.infrastructure.database.session import SessionLocal


HANDOFF_SCHEMA = "trading_ops.stock_research_handoff_input.v0"
SAFE_NEWS_SCHEMA = "alphadesk.safe_news_export.v0"
DEFAULT_LIMIT = 24

FORBIDDEN_KEYS = {
    "account_id",
    "analyst_rating",
    "api_key",
    "body",
    "body_text",
    "buy_sell_recommendation",
    "content",
    "content_hash",
    "exact_balance",
    "html",
    "internal_url",
    "investment_advice",
    "link",
    "link_hash",
    "local_path",
    "order_id",
    "price_target",
    "rating",
    "raw_article",
    "raw_body",
    "raw_csv",
    "raw_filing",
    "raw_html",
    "raw_news_article",
    "raw_report",
    "recommendation",
    "secret",
    "secret_key",
    "source_url",
    "target_price",
    "text",
    "token",
    "url",
    "viewer_url",
    "xbrl",
}

FORBIDDEN_KEY_MARKERS = (
    "url",
    "link",
    "body",
    "content",
    "html",
    "raw_",
    "api_key",
    "secret",
    "token",
    "account_id",
    "order_id",
)

PRIVATE_VALUE_RE = re.compile(
    r"([A-Za-z]:\\|/Users/|/home/|\\\\|https?://|api[_-]?key|secret|token|"
    r"account[_-]?id|exact[_-]?balance|internal[_-]?url|server[_-]?url|"
    r"local[_-]?path|order[_-]?id)",
    re.IGNORECASE,
)

ADVICE_TEXT_RE = re.compile(
    r"\b(buy|sell|hold|target price|price target|recommendation)\b|"
    r"(매수|매도|보유|목표가|목표주가|투자의견|추천)",
    re.IGNORECASE,
)


def default_output_path() -> Path:
    projects_root = Path(__file__).resolve().parents[3]
    return (
        projects_root
        / "trading-ops-ai-assistant"
        / "data"
        / "local"
        / "stock_research_handoff"
        / "reviewed_stock_research_handoff.json"
    )


def build_handoff(*, limit: int, source_type: str) -> tuple[dict[str, Any], dict[str, int]]:
    with SessionLocal() as db:
        watchlist_rows = (
            db.query(WatchlistItemORM)
            .order_by(WatchlistItemORM.created_at.desc(), WatchlistItemORM.symbol.asc())
            .all()
        )
        watchlist_symbols = _watchlist_rows(watchlist_rows)

        query = db.query(AnalysisLogORM).filter(
            AnalysisLogORM.summary.isnot(None),
            AnalysisLogORM.summary != "",
        )
        if source_type.upper() != "ALL":
            query = query.filter(func.upper(AnalysisLogORM.source_type) == source_type.upper())
        analysis_rows = query.order_by(AnalysisLogORM.analyzed_at.desc()).limit(limit * 3).all()

    articles: list[dict[str, Any]] = []
    skipped_rows = 0
    for log in analysis_rows:
        row = _article_row(log)
        if _row_should_be_skipped(row):
            skipped_rows += 1
            continue
        articles.append(row)
        if len(articles) >= limit:
            break

    payload = {
        "schema": HANDOFF_SCHEMA,
        "fixture_mode": "reviewed_real_local_fixture",
        "stock_universe": {
            "held_symbols": [],
            "watchlist_symbols": watchlist_symbols,
            "strategy_symbols": [],
            "hot_candidates": [],
            "baseline_symbols": [],
            "on_demand_symbols": [],
            "previous_tiers": [],
        },
        "alpha_desk_safe_news_export": {
            "schema": SAFE_NEWS_SCHEMA,
            "articles": articles,
        },
    }

    safety_issues = find_safety_issues(payload)
    if safety_issues:
        joined = "; ".join(safety_issues[:5])
        raise ValueError(f"safe export blocked by safety scan: {joined}")

    counts = {
        "watchlist_symbol_count": len(watchlist_symbols),
        "article_count": len(articles),
        "skipped_row_count": skipped_rows,
    }
    return payload, counts


def write_handoff(output: Path, payload: dict[str, Any]) -> None:
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )


def _watchlist_rows(rows: list[WatchlistItemORM]) -> list[dict[str, str]]:
    seen: set[str] = set()
    symbols: list[dict[str, str]] = []
    for item in rows:
        symbol = _stock_symbol(item.symbol)
        if not symbol or symbol in seen:
            continue
        row = {
            "symbol": symbol,
            "company_name": _compact_text(item.name, 100),
            "theme": "watchlist_monitoring",
        }
        if not _row_should_be_skipped(row):
            symbols.append(row)
            seen.add(symbol)
    return symbols


def _article_row(log: AnalysisLogORM) -> dict[str, str]:
    symbol = _stock_symbol(log.symbol)
    company_name = _compact_text(log.name, 100)
    source = _compact_text(log.source_name or log.source_type or "AlphaDeskNews", 100)
    summary = _compact_text(log.summary, 900)
    source_kind = _safe_label(log.source_type or "NEWS")
    return {
        "source": source,
        "title": _compact_text(f"{company_name or symbol} Alpha Desk news summary", 180),
        "snippet": summary,
        "published_at": _iso(log.article_published_at or log.analyzed_at),
        "stock_symbol": symbol,
        "stock_name": company_name,
        "theme": f"alpha_desk_{source_kind}",
        "event_label": "reviewed_ai_summary",
    }


def _row_should_be_skipped(row: dict[str, Any]) -> bool:
    if find_safety_issues(row):
        return True
    for value in row.values():
        if isinstance(value, str) and ADVICE_TEXT_RE.search(value):
            return True
    return False


def find_safety_issues(value: Any) -> list[str]:
    issues: list[str] = []

    def visit(node: Any, path: str) -> None:
        if isinstance(node, dict):
            for key, child in node.items():
                key_text = str(key)
                key_lower = key_text.lower()
                key_path = f"{path}.{key_text}" if path else key_text
                if key_lower in FORBIDDEN_KEYS or any(
                    marker in key_lower for marker in FORBIDDEN_KEY_MARKERS
                ):
                    issues.append(key_path)
                visit(child, key_path)
            return
        if isinstance(node, list):
            for index, child in enumerate(node):
                visit(child, f"{path}[{index}]")
            return
        if isinstance(node, str) and PRIVATE_VALUE_RE.search(node):
            issues.append(path)

    visit(value, "")
    return sorted(set(issues))


def _compact_text(value: Any, limit: int) -> str:
    text = " ".join(str(value or "").split())
    return text[:limit]


def _stock_symbol(value: Any) -> str:
    text = _compact_text(value, 20).upper()
    return re.sub(r"[^0-9A-Z.:-]", "", text)


def _safe_label(value: Any) -> str:
    text = _compact_text(value, 80).lower()
    text = re.sub(r"[^a-z0-9]+", "_", text).strip("_")
    return text or "news"


def _iso(value: datetime | None) -> str:
    dt = value or datetime.now(timezone.utc)
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(timezone.utc).isoformat().replace("+00:00", "Z")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--output",
        type=Path,
        default=default_output_path(),
        help="Output JSON path. Defaults to the Trading Ops local handoff path.",
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=DEFAULT_LIMIT,
        help="Maximum safe news rows to export.",
    )
    parser.add_argument(
        "--source-type",
        default="NEWS",
        help="Analysis log source_type to export, or ALL.",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    if args.limit < 1:
        raise ValueError("--limit must be at least 1")
    payload, counts = build_handoff(limit=min(args.limit, 50), source_type=args.source_type)
    write_handoff(args.output, payload)
    print(
        json.dumps(
            {
                "status": "ok",
                "output_file": args.output.name,
                **counts,
            },
            ensure_ascii=False,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
