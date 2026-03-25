import time
from datetime import datetime, timedelta
from hashlib import sha256
from typing import List

import httpx

from app.domains.stock_collector.application.usecase.collector_port import CollectorPort
from app.domains.stock_collector.domain.entity.raw_article import RawArticle
from app.infrastructure.config.settings import get_settings


class DartCollectorAdapter(CollectorPort):
    DART_API_URL = "https://opendart.fss.or.kr/api/list.json"

    def collect(self, symbol: str, stock_name: str, corp_code: str) -> List[RawArticle]:
        settings = get_settings()

        params = {
            "crtfc_key": settings.dart_api_key,
            "corp_code": corp_code,
            "bgn_de": (datetime.now() - timedelta(days=30)).strftime("%Y%m%d"),
            "end_de": datetime.now().strftime("%Y%m%d"),
            "page_no": "1",
            "page_count": "10",
        }

        try:
            time.sleep(1)
            response = httpx.get(self.DART_API_URL, params=params, timeout=10.0)
            response.raise_for_status()
            data = response.json()
        except httpx.TimeoutException:
            import logging
            logging.getLogger(__name__).warning(f"[DartCollector] 요청 타임아웃: symbol={symbol}")
            return []
        except httpx.HTTPError as e:
            import logging
            logging.getLogger(__name__).warning(f"[DartCollector] API 요청 실패: symbol={symbol}, error={e}")
            return []

        dart_status = data.get("status")
        if dart_status != "000":
            import logging
            logging.getLogger(__name__).info(f"[DartCollector] 공시 없음: symbol={symbol}, dart_status={dart_status}")
            return []

        articles = []
        now = datetime.now().isoformat()

        for item in data.get("list", []):
            rcp_no = item.get("rcept_no", "")
            body_text = f"{item.get('report_nm', '')} - {item.get('flr_nm', '')}"
            content = body_text.encode()

            articles.append(
                RawArticle(
                    source_type="DISCLOSURE",
                    source_name="DART",
                    source_doc_id=rcp_no,
                    url=f"https://dart.fss.or.kr/dsaf001/main.do?rcpNo={rcp_no}",
                    title=item.get("report_nm", ""),
                    body_text=body_text,
                    published_at=item.get("rcept_dt", ""),
                    collected_at=now,
                    symbol=symbol,
                    market=item.get("corp_cls", ""),
                    content_hash=f"sha256:{sha256(content).hexdigest()}",
                    collector_version="collector-v1.0.0",
                    status="COLLECTED",
                    author="금융감독원 전자공시시스템",
                    meta={
                        "report_type": item.get("report_nm", ""),
                        "corp_name": item.get("corp_name", ""),
                        "rcp_no": rcp_no,
                    },
                )
            )

        return articles
