import logging

from app.domains.stock.application.usecase.dart_corp_code_port import DartCorpCodePort
from app.domains.stock.application.usecase.stock_repository_port import StockRepositoryPort

logger = logging.getLogger(__name__)


class SyncCorpCodeUseCase:

    def __init__(self, dart_port: DartCorpCodePort, repository: StockRepositoryPort):
        self._dart_port = dart_port
        self._repository = repository

    def execute(self) -> int:
        stocks = self._dart_port.fetch_all()
        count = self._repository.bulk_upsert(stocks)
        logger.info(f"[SyncCorpCode] {count}개 종목 동기화 완료")
        return count
