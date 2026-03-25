from typing import List, Optional

from sqlalchemy.orm import Session

from app.domains.pipeline.application.response.analysis_log_response import AnalysisLogResponse
from app.domains.pipeline.application.usecase.analysis_log_repository_port import AnalysisLogRepositoryPort
from app.domains.pipeline.infrastructure.orm.analysis_log_orm import AnalysisLogORM


class AnalysisLogRepositoryImpl(AnalysisLogRepositoryPort):
    def __init__(self, db: Session):
        self._db = db

    def save_all(self, logs: List[AnalysisLogResponse], account_id: Optional[int] = None) -> None:
        for log in logs:
            orm = AnalysisLogORM(
                analyzed_at=log.analyzed_at,
                symbol=log.symbol,
                name=log.name,
                summary=log.summary,
                tags=log.tags,
                sentiment=log.sentiment,
                sentiment_score=log.sentiment_score,
                confidence=log.confidence,
                account_id=account_id,
            )
            self._db.add(orm)
        self._db.commit()

    def find_recent(self, limit: int = 50, account_id: Optional[int] = None) -> List[AnalysisLogResponse]:
        query = self._db.query(AnalysisLogORM)
        if account_id is not None:
            query = query.filter(AnalysisLogORM.account_id == account_id)
        orms = query.order_by(AnalysisLogORM.analyzed_at.desc()).limit(limit).all()
        return [
            AnalysisLogResponse(
                analyzed_at=orm.analyzed_at,
                symbol=orm.symbol,
                name=orm.name,
                summary=orm.summary,
                tags=orm.tags or [],
                sentiment=orm.sentiment,
                sentiment_score=orm.sentiment_score,
                confidence=orm.confidence,
                account_id=orm.account_id,
            )
            for orm in orms
        ]
