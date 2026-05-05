"""Alpha Vantage daily price lookup for US market heatmaps."""

from __future__ import annotations

import logging
from typing import List, Tuple

import httpx

logger = logging.getLogger(__name__)

ALPHA_VANTAGE_URL = "https://www.alphavantage.co/query"


def fetch_daily_closes_from_alpha_vantage(
    symbol: str,
    outputsize: int,
    api_key: str,
) -> tuple[list[tuple[str, float]] | None, str | None, str | None]:
    """Return ([(YYYY-MM-DD, close)], error_code, error_message)."""
    if not api_key:
        return None, "NO_PROVIDER_KEY", "Alpha Vantage API key is not configured."

    params = {
        "function": "TIME_SERIES_DAILY",
        "symbol": symbol.strip().upper(),
        "outputsize": "full" if outputsize > 100 else "compact",
        "apikey": api_key,
    }

    try:
        res = httpx.get(ALPHA_VANTAGE_URL, params=params, timeout=20.0)
        res.raise_for_status()
        data = res.json()
    except httpx.HTTPStatusError as e:
        status = e.response.status_code if e.response is not None else "?"
        logger.warning("[AlphaVantageDaily] HTTP %s symbol=%s", status, symbol)
        return None, "PROVIDER_HTTP_ERROR", "US daily price API request failed."
    except Exception as e:
        logger.warning("[AlphaVantageDaily] request failed symbol=%s error=%s", symbol, type(e).__name__)
        return None, "PROVIDER_ERROR", "US daily price API request failed."

    if not isinstance(data, dict):
        return None, "NO_DATA", "US daily price data was not returned."

    provider_message = data.get("Error Message") or data.get("Information") or data.get("Note")
    if provider_message:
        logger.warning("[AlphaVantageDaily] API message symbol=%s message=%s", symbol, provider_message)
        return None, "PROVIDER_API_ERROR", str(provider_message)

    series = data.get("Time Series (Daily)")
    if not isinstance(series, dict):
        return None, "NO_DATA", "US daily price data was not returned."

    out: List[Tuple[str, float]] = []
    for day, row in series.items():
        if not isinstance(row, dict):
            continue
        close_s = str(row.get("4. close") or "").strip()
        if not close_s:
            continue
        try:
            close_v = float(close_s)
        except ValueError:
            continue
        out.append((str(day), close_v))

    if not out:
        return None, "NO_DATA", "US daily price data was not returned."

    out.sort(key=lambda x: x[0])
    return out, None, None
