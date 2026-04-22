from datetime import datetime, timedelta
from typing import Optional

from sqlalchemy.orm import Session

from app.domains.investment.infrastructure.orm.analysis_cache_orm import AnalysisCacheORM

CACHE_TTL_HOURS = 1


class AnalysisCacheRepository:
    def __init__(self, db: Session) -> None:
        self._db = db

    def find_valid(self, symbol: str) -> Optional[AnalysisCacheORM]:
        return (
            self._db.query(AnalysisCacheORM)
            .filter(
                AnalysisCacheORM.symbol == symbol,
                AnalysisCacheORM.expires_at > datetime.now(),
            )
            .order_by(AnalysisCacheORM.created_at.desc())
            .first()
        )

    def save(self, symbol: str, query: str, answer: str) -> AnalysisCacheORM:
        try:
            now = datetime.now()
            orm = AnalysisCacheORM(
                symbol=symbol,
                query=query,
                answer=answer,
                created_at=now,
                expires_at=now + timedelta(hours=CACHE_TTL_HOURS),
            )
            self._db.add(orm)
            self._db.commit()
            self._db.refresh(orm)
            return orm
        except Exception:
            self._db.rollback()
            raise
