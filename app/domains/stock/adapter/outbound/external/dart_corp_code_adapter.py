import io
import logging
import zipfile
from typing import List
from xml.etree import ElementTree

import httpx

from app.domains.stock.application.usecase.dart_corp_code_port import DartCorpCodePort
from app.domains.stock.domain.entity.stock import Stock
from app.infrastructure.config.settings import get_settings

logger = logging.getLogger(__name__)

DART_CORP_CODE_URL = "https://opendart.fss.or.kr/api/corpCode.xml"

MARKET_MAP = {
    "Y": "KOSPI",
    "K": "KOSDAQ",
    "N": "KONEX",
    "E": "ETC",
}


class DartCorpCodeAdapter(DartCorpCodePort):

    def fetch_all(self) -> List[Stock]:
        settings = get_settings()
        params = {"crtfc_key": settings.dart_api_key}

        response = httpx.get(DART_CORP_CODE_URL, params=params, timeout=30.0)
        response.raise_for_status()

        # ZIP 파일 압축 해제 → XML 파싱
        with zipfile.ZipFile(io.BytesIO(response.content)) as z:
            xml_filename = [f for f in z.namelist() if f.endswith(".xml")][0]
            xml_content = z.read(xml_filename)

        root = ElementTree.fromstring(xml_content)
        stocks = []

        for item in root.findall("list"):
            corp_code = item.findtext("corp_code", "").strip()
            name = item.findtext("corp_name", "").strip()
            symbol = item.findtext("stock_code", "").strip()
            market_raw = item.findtext("corp_cls", "").strip()

            # 상장 종목만 (symbol 없으면 비상장)
            if not symbol:
                continue

            stocks.append(Stock(
                symbol=symbol,
                name=name,
                market=MARKET_MAP.get(market_raw, market_raw),
                corp_code=corp_code,
            ))

        logger.info(f"[DART] 전체 상장사 {len(stocks)}개 로드 완료")
        return stocks
