from typing import List, Optional

from sqlalchemy import or_
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
                source_type=log.source_type,
                account_id=account_id,
                url=getattr(log, "url", None),
            )
            self._db.add(orm)
        self._db.commit()

    def find_latest_per_symbol(self, source_types: List[str], account_id: Optional[int] = None) -> List[AnalysisLogResponse]:
        query = self._db.query(AnalysisLogORM)
        if account_id is not None:
            query = query.filter(AnalysisLogORM.account_id == account_id)
        # NULL source_type은 NEWS로 간주 (컬럼 추가 이전 레코드 호환)
        if "NEWS" in source_types:
            query = query.filter(
                or_(AnalysisLogORM.source_type.in_(source_types), AnalysisLogORM.source_type.is_(None))
            )
        else:
            query = query.filter(AnalysisLogORM.source_type.in_(source_types))
        orms = query.order_by(AnalysisLogORM.analyzed_at.desc()).all()
        seen: set = set()
        result = []
        for orm in orms:
            if orm.symbol not in seen:
                seen.add(orm.symbol)
                result.append(AnalysisLogResponse(
                    analyzed_at=orm.analyzed_at,
                    symbol=orm.symbol,
                    name=orm.name,
                    summary=orm.summary,
                    tags=orm.tags or [],
                    sentiment=orm.sentiment,
                    sentiment_score=orm.sentiment_score,
                    confidence=orm.confidence,
                    source_type=orm.source_type or "NEWS",
                    account_id=orm.account_id,
                    url=orm.url,
                ))
        return result

    def find_latest_by_symbols(self, symbols: List[str]) -> List[AnalysisLogResponse]:
        upper_symbols = [s.upper() for s in symbols]
        orms = (
            self._db.query(AnalysisLogORM)
            .filter(AnalysisLogORM.symbol.in_(upper_symbols))
            .order_by(AnalysisLogORM.analyzed_at.desc())
            .all()
        )
        seen: set = set()
        result = []
        for orm in orms:
            if orm.symbol not in seen:
                seen.add(orm.symbol)
                result.append(AnalysisLogResponse(
                    analyzed_at=orm.analyzed_at,
                    symbol=orm.symbol,
                    name=orm.name,
                    summary=orm.summary,
                    tags=orm.tags or [],
                    sentiment=orm.sentiment,
                    sentiment_score=orm.sentiment_score,
                    confidence=orm.confidence,
                    source_type=orm.source_type or "NEWS",
                    account_id=orm.account_id,
                    url=orm.url,
                ))
        return result

    def find_by_symbol(self, symbol: str, limit: int = 20) -> List[AnalysisLogResponse]:
        orms = (
            self._db.query(AnalysisLogORM)
            .filter(AnalysisLogORM.symbol == symbol.upper())
            .order_by(AnalysisLogORM.analyzed_at.desc())
            .limit(limit)
            .all()
        )
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
                source_type=orm.source_type or "NEWS",
                account_id=orm.account_id,
                url=orm.url,
            )
            for orm in orms
        ]

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
                source_type=orm.source_type or "NEWS",
                account_id=orm.account_id,
                url=orm.url,
            )
            for orm in orms
        ]
