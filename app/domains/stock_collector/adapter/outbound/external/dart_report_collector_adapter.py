import logging
import time
from datetime import datetime
from hashlib import sha256
from typing import List, Optional, Tuple

import httpx

from app.domains.stock_collector.application.usecase.collector_port import CollectorPort
from app.domains.stock_collector.domain.entity.raw_article import RawArticle
from app.infrastructure.config.settings import get_settings

logger = logging.getLogger(__name__)

KEY_ACCOUNTS = {"매출액", "영업이익", "당기순이익", "자산총계", "부채총계", "자본총계"}


def _get_recent_reprt_code(now: datetime) -> Tuple[str, str]:
    """현재 날짜 기준으로 가장 최근에 공시됐을 보고서 코드와 기간 레이블 반환"""
    month = now.month
    year = now.year
    if month <= 4:
        return "11014", f"{year - 1}년 3분기"
    elif month <= 6:
        return "11013", f"{year}년 1분기"
    elif month <= 9:
        return "11012", f"{year}년 반기"
    elif month <= 11:
        return "11014", f"{year}년 3분기"
    else:
        return "11011", f"{year}년 사업보고서"


def _format_amount(value: str) -> str:
    try:
        num = int(value.replace(",", "").replace("-", "0"))
        if abs(num) >= 1_000_000_000_000:
            return f"{num / 1_000_000_000_000:.2f}조원"
        elif abs(num) >= 100_000_000:
            return f"{num / 100_000_000:.0f}억원"
        else:
            return f"{num:,}원"
    except Exception:
        return value or "-"


class DartReportCollectorAdapter(CollectorPort):
    DART_FINANCIAL_URL = "https://opendart.fss.or.kr/api/fnlttSinglAcnt.json"

    def collect(self, symbol: str, stock_name: str, corp_code: str) -> List[RawArticle]:
        if not corp_code:
            logger.warning(f"[DartReport] corp_code 없음: {symbol}")
            return []

        settings = get_settings()
        now = datetime.now()
        reprt_code, period_label = _get_recent_reprt_code(now)

        # 가장 최근 기간 먼저, 없으면 전년도 같은 기간 시도
        for bsns_year in [now.year, now.year - 1]:
            article = self._fetch_report_article(
                api_key=settings.dart_api_key,
                corp_code=corp_code,
                symbol=symbol,
                bsns_year=bsns_year,
                reprt_code=reprt_code,
                period_label=period_label,
            )
            if article:
                return [article]

        logger.warning(f"[DartReport] {symbol} 재무데이터 없음")
        return []

    def _fetch_report_article(
        self,
        api_key: str,
        corp_code: str,
        symbol: str,
        bsns_year: int,
        reprt_code: str,
        period_label: str,
    ) -> Optional[RawArticle]:
        for fs_div in ("CFS", "OFS"):  # 연결재무제표 → 별도재무제표 순서로 시도
            params = {
                "crtfc_key": api_key,
                "corp_code": corp_code,
                "bsns_year": str(bsns_year),
                "reprt_code": reprt_code,
                "fs_div": fs_div,
            }
            try:
                time.sleep(1)
                resp = httpx.get(self.DART_FINANCIAL_URL, params=params, timeout=15.0)
                resp.raise_for_status()
                data = resp.json()
            except httpx.TimeoutException:
                logger.warning(f"[DartReport] 요청 타임아웃: symbol={symbol}, year={bsns_year}")
                return None
            except httpx.HTTPError as e:
                logger.warning(f"[DartReport] API 요청 실패: symbol={symbol}, year={bsns_year}, error={e}")
                return None

            if data.get("status") != "000" or not data.get("list"):
                continue

            financial_data = {}
            corp_name = ""

            for item in data["list"]:
                account = item.get("account_nm", "")
                if not corp_name:
                    corp_name = item.get("corp_name", "")
                if account in KEY_ACCOUNTS:
                    financial_data[account] = {
                        "current": item.get("thstrm_amount", ""),
                        "previous": item.get("frmtrm_amount", ""),
                    }

            if not financial_data:
                continue

            lines = [f"[{corp_name} {period_label} 재무제표 요약]", ""]
            for account in ["매출액", "영업이익", "당기순이익", "자산총계", "부채총계", "자본총계"]:
                if account in financial_data:
                    current = _format_amount(financial_data[account]["current"])
                    previous = _format_amount(financial_data[account]["previous"])
                    lines.append(f"- {account}: {current} (전기: {previous})")

            # 영업이익률 계산
            try:
                revenue = int(financial_data.get("매출액", {}).get("current", "0").replace(",", "") or "0")
                operating = int(financial_data.get("영업이익", {}).get("current", "0").replace(",", "") or "0")
                if revenue > 0:
                    margin = operating / revenue * 100
                    lines.append(f"- 영업이익률: {margin:.1f}%")
            except Exception:
                pass

            body_text = "\n".join(lines)
            title = f"{corp_name} {period_label} 재무실적 요약"
            now = datetime.now()
            content = body_text.encode()

            return RawArticle(
                source_type="REPORT",
                source_name="DART_FINANCIAL",
                source_doc_id=f"dart-fin-{symbol}-{bsns_year}-{reprt_code}-{fs_div}",
                url=f"https://dart.fss.or.kr/",
                title=title,
                body_text=body_text,
                published_at=now.isoformat(),
                collected_at=now.isoformat(),
                symbol=symbol,
                market="KR",
                content_hash=f"sha256:{sha256(content).hexdigest()}",
                collector_version="collector-v1.0.0",
                status="COLLECTED",
                author="금융감독원 전자공시시스템",
                meta={"report_type": "FINANCIAL_STATEMENT", "period": period_label, "fs_div": fs_div},
            )

        return None
