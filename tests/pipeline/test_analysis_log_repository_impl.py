from datetime import datetime, timedelta

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.domains.pipeline.adapter.outbound.persistence.analysis_log_repository_impl import AnalysisLogRepositoryImpl
from app.domains.pipeline.application.response.analysis_log_response import AnalysisLogResponse
from app.domains.pipeline.infrastructure.orm.analysis_log_orm import AnalysisLogORM
from app.infrastructure.database.session import Base


def _session():
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(bind=engine, tables=[AnalysisLogORM.__table__])
    return sessionmaker(bind=engine)()


def _log(symbol: str, summary: str, analyzed_at: datetime) -> AnalysisLogResponse:
    return AnalysisLogResponse(
        analyzed_at=analyzed_at,
        symbol=symbol,
        name=symbol,
        summary=summary,
        tags=[],
        sentiment="NEUTRAL",
        sentiment_score=0.0,
        confidence=0.8,
        source_type="NEWS",
    )


def test_save_all_skips_empty_summaries():
    db = _session()
    repo = AnalysisLogRepositoryImpl(db)

    repo.save_all(
        [
            _log("005930", "", datetime(2026, 5, 12, 9, 0, 0)),
            _log("000660", "non-empty", datetime(2026, 5, 12, 9, 1, 0)),
        ],
        account_id=1,
    )

    assert db.query(AnalysisLogORM).count() == 1
    assert db.query(AnalysisLogORM).one().summary == "non-empty"


def test_find_latest_per_symbol_ignores_existing_empty_latest_log():
    db = _session()
    repo = AnalysisLogRepositoryImpl(db)
    older = datetime(2026, 5, 12, 8, 0, 0)
    newer = older + timedelta(hours=1)

    db.add(
        AnalysisLogORM(
            analyzed_at=older,
            symbol="005930",
            name="삼성전자",
            summary="older non-empty summary",
            tags=[],
            sentiment="NEUTRAL",
            sentiment_score=0.0,
            confidence=0.8,
            source_type="NEWS",
            account_id=1,
        )
    )
    db.add(
        AnalysisLogORM(
            analyzed_at=newer,
            symbol="005930",
            name="삼성전자",
            summary="",
            tags=[],
            sentiment="NEUTRAL",
            sentiment_score=0.0,
            confidence=0.8,
            source_type="NEWS",
            account_id=1,
        )
    )
    db.commit()

    result = repo.find_latest_per_symbol(["NEWS"], account_id=1)

    assert len(result) == 1
    assert result[0].summary == "older non-empty summary"
