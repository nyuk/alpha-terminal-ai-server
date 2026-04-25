from sqlalchemy.orm import Session

from app.domains.analytics.infrastructure.orm.event_orm import EventORM


class RecordEventUseCase:

    def __init__(self, db: Session):
        self._db = db

    def execute(self, account_id: int, event_type: str, campaign: str | None = None) -> None:
        event = EventORM(account_id=account_id, event_type=event_type, campaign=campaign)
        self._db.add(event)
        self._db.commit()
