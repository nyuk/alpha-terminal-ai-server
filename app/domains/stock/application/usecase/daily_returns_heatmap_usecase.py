"""일별 등락 bucket 시계열 + 배치 응답 (BL-BE-13, BL-BE-14)."""

from __future__ import annotations

import logging
import time
from datetime import date, timedelta
from typing import Dict, List, Optional, Tuple

from app.domains.stock.adapter.outbound.external.data_go_kr_daily_price_adapter import (
    fetch_daily_closes_from_data_go_kr,
)
from app.domains.stock.adapter.outbound.external.alpha_vantage_daily_price_adapter import (
    fetch_daily_closes_from_alpha_vantage,
)
from app.domains.stock.adapter.outbound.external.twelve_data_daily_price_adapter import (
    fetch_daily_closes_from_twelve_data,
)
from app.domains.stock.application.response.daily_returns_heatmap_response import (
    DailyReturnsHeatmapResponse,
    HeatmapErrorItem,
    HeatmapItem,
    HeatmapSummary,
)
from app.domains.stock.application.usecase.stock_repository_port import StockRepositoryPort
from app.infrastructure.cache.heatmap_redis_cache import get_closes as redis_get_closes
from app.infrastructure.cache.heatmap_redis_cache import set_closes as redis_set_closes
from app.infrastructure.cache.redis_client import redis_client

logger = logging.getLogger(__name__)

_CACHE_TTL_SEC = 1800.0
_cache: Dict[str, Tuple[float, List[Tuple[str, float]]]] = {}
_KR_MARKETS = {"KOSPI", "KOSDAQ", "KONEX"}
_US_MARKETS = {"NASDAQ", "NYSE"}


def _cache_get(key: str) -> Optional[List[Tuple[str, float]]]:
    """캐시 히트 시 [(date, close)], 미스 시 None."""
    now = time.monotonic()
    ent = _cache.get(key)
    if not ent:
        return None
    exp, val = ent
    if now >= exp:
        del _cache[key]
        return None
    return val


def _cache_set(key: str, val: List[Tuple[str, float]]) -> None:
    _cache[key] = (time.monotonic() + _CACHE_TTL_SEC, val)


def _pct_to_bucket(pct: float) -> int:
    """전일 대비 등락률(%) → -2..2."""
    if abs(pct) < 0.1:
        return 0
    if pct >= 2.0:
        return 2
    if pct >= 0.5:
        return 1
    if pct <= -2.0:
        return -2
    if pct <= -0.5:
        return -1
    return 0


def _series_from_closes(
    closes_by_day: List[Tuple[str, float]],
    max_trading_days: int,
) -> Tuple[List[Tuple[str, int]], str | None]:
    pairs = sorted(closes_by_day, key=lambda x: x[0])
    out: List[Tuple[str, int]] = []
    for i in range(1, len(pairs)):
        _d0, c0 = pairs[i - 1]
        d1, c1 = pairs[i]
        if c0 <= 0:
            continue
        pct = (c1 - c0) / c0 * 100.0
        out.append((d1, _pct_to_bucket(pct)))
    tail = out[-max_trading_days:] if len(out) > max_trading_days else out
    as_day = tail[-1][0] if tail else None
    return tail, as_day


def _summarize(series: List[Tuple[str, int]]) -> HeatmapSummary:
    up = down = flat = 0
    for _, b in series:
        if b > 0:
            up += 1
        elif b < 0:
            down += 1
        else:
            flat += 1
    return HeatmapSummary(up=up, down=down, flat=flat)


class DailyReturnsHeatmapUseCase:
    def __init__(
        self,
        repository: StockRepositoryPort,
        data_go_kr_service_key: str,
        twelve_data_api_key: str,
        alpha_vantage_api_key: str = "",
        *,
        heatmap_redis_cache_enabled: bool = True,
    ):
        self._repository = repository
        self._data_go_kr_service_key = data_go_kr_service_key or ""
        self._twelve_data_api_key = twelve_data_api_key or ""
        self._alpha_vantage_api_key = alpha_vantage_api_key or ""
        self._heatmap_redis_cache_enabled = heatmap_redis_cache_enabled

    @staticmethod
    def _twelve_data_exchange(market: str) -> str | None:
        if market == "NASDAQ":
            return "NASDAQ"
        if market == "NYSE":
            return "NYSE"
        return None

    @staticmethod
    def _infer_market(symbol: str, db_market: Optional[str]) -> str:
        market = (db_market or "").upper()
        if market in _KR_MARKETS | _US_MARKETS:
            return market
        s = symbol.strip().upper()
        if s.isdigit() and len(s) == 6:
            return "KOSPI"
        logger.debug(
            "[Heatmap] market inferred as NASDAQ (no DB/KR rule) symbol=%s db_market=%r",
            symbol,
            db_market,
        )
        return "NASDAQ"

    def _provider_for_market(self, market: str) -> str:
        if market in _KR_MARKETS:
            return "DATA_GO_KR"
        if market in _US_MARKETS:
            if self._alpha_vantage_api_key:
                return "ALPHA_VANTAGE"
            if self._twelve_data_api_key:
                return "TWELVE_DATA"
            return "ALPHA_VANTAGE"
        return "UNSUPPORTED"

    def execute(self, symbols: List[str], weeks: int) -> DailyReturnsHeatmapResponse:
        weeks = max(1, min(weeks, 13))
        unique = list(dict.fromkeys(s.strip() for s in symbols if s.strip()))
        errors: List[HeatmapErrorItem] = []
        items: List[HeatmapItem] = []
        global_as_of: str | None = None

        end_day = date.today()
        begin_day = end_day - timedelta(days=weeks * 7 + 14)
        max_trading_days = weeks * 5 + 5
        begin_ymd = begin_day.strftime("%Y%m%d")
        end_ymd = end_day.strftime("%Y%m%d")
        us_outputsize = max(weeks * 8, 45)

        for raw_sym in unique:
            db_market = self._repository.find_market_by_symbol(raw_sym)
            market_label = self._infer_market(raw_sym, db_market)
            provider = self._provider_for_market(market_label)
            cache_key = f"{provider}|{raw_sym.upper()}|{weeks}|{end_day.isoformat()}"

            closes: List[Tuple[str, float]] | None = _cache_get(cache_key)
            if closes is None and self._heatmap_redis_cache_enabled:
                redis_closes = redis_get_closes(redis_client, cache_key)
                if redis_closes is not None:
                    closes = redis_closes
                    _cache_set(cache_key, closes)

            if closes is not None:
                error_code = None
                error_message = None
            else:
                if provider == "DATA_GO_KR":
                    closes, error_code, error_message = fetch_daily_closes_from_data_go_kr(
                        symbol=raw_sym.zfill(6),
                        begin_date=begin_ymd,
                        end_date=end_ymd,
                        service_key=self._data_go_kr_service_key,
                        num_rows=max(weeks * 10, 100),
                    )
                elif provider == "ALPHA_VANTAGE":
                    closes, error_code, error_message = fetch_daily_closes_from_alpha_vantage(
                        symbol=raw_sym,
                        outputsize=us_outputsize,
                        api_key=self._alpha_vantage_api_key,
                    )
                elif provider == "TWELVE_DATA":
                    closes, error_code, error_message = fetch_daily_closes_from_twelve_data(
                        symbol=raw_sym,
                        outputsize=us_outputsize,
                        api_key=self._twelve_data_api_key,
                        exchange=self._twelve_data_exchange(market_label),
                    )
                else:
                    closes = None
                    error_code = "UNSUPPORTED_MARKET"
                    error_message = "지원하지 않는 시장입니다."

                if closes is not None:
                    _cache_set(cache_key, closes)
                    if self._heatmap_redis_cache_enabled:
                        redis_set_closes(redis_client, cache_key, closes, ttl_sec=int(_CACHE_TTL_SEC))

            if closes is None:
                errors.append(
                    HeatmapErrorItem(
                        symbol=raw_sym,
                        code=error_code or "NO_DATA",
                        message=error_message or "일봉 데이터를 가져오지 못했습니다.",
                    )
                )
                continue

            series, as_day = _series_from_closes(closes, max_trading_days)
            if not series:
                errors.append(
                    HeatmapErrorItem(symbol=raw_sym, code="NO_DATA", message="유효한 일봉 구간이 없습니다.")
                )
                continue

            if as_day and (global_as_of is None or as_day > global_as_of):
                global_as_of = as_day

            items.append(
                HeatmapItem(
                    symbol=raw_sym,
                    market=market_label,
                    series=series,
                    summary=_summarize(series),
                )
            )

        return DailyReturnsHeatmapResponse(as_of=global_as_of, weeks=weeks, items=items, errors=errors)
