"""관리자 대시보드 통계 UseCase."""
from datetime import datetime, timedelta, date

from sqlalchemy import func, distinct, case
from sqlalchemy.orm import Session

from app.domains.account.infrastructure.orm.account_orm import AccountORM
from app.domains.analytics.infrastructure.orm.event_orm import EventORM
from app.domains.admin.application.response.admin_dashboard_stats_response import (
    AdminDashboardStatsResponse,
    RetentionPoint,
)


class GetAdminDashboardStatsUseCase:

    def __init__(self, db: Session):
        self._db = db

    def execute(self) -> AdminDashboardStatsResponse:
        now = datetime.now()
        today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
        week_start = today_start - timedelta(days=now.weekday())

        total_users = self._db.query(AccountORM).count()

        new_users_today = (
            self._db.query(AccountORM)
            .filter(AccountORM.created_at >= today_start)
            .count()
        )

        new_users_this_week = (
            self._db.query(AccountORM)
            .filter(AccountORM.created_at >= week_start)
            .count()
        )

        retention = self._calc_retention()
        activation_rate = self._calc_activation_rate(total_users)

        return AdminDashboardStatsResponse(
            total_users=total_users,
            new_users_today=new_users_today,
            new_users_this_week=new_users_this_week,
            retention=retention,
            avg_dwell_time_seconds=None,
            ctr=activation_rate,  # activation_rate을 ctr 필드로 재활용 (FE 레이블은 이승욱님이 수정)
        )

    def _calc_retention(self) -> list[RetentionPoint]:
        """D-1 ~ D-14 Retention: 가입 D+N일에 app_open 이벤트가 있는 비율."""
        points: list[RetentionPoint] = []
        today = date.today()

        for day in range(1, 15):
            cohort_date = today - timedelta(days=day)
            cohort_start = datetime.combine(cohort_date, datetime.min.time())
            cohort_end = cohort_start + timedelta(days=1)
            target_start = cohort_start + timedelta(days=day)
            target_end = target_start + timedelta(days=1)

            cohort_ids = (
                self._db.query(AccountORM.id)
                .filter(AccountORM.created_at >= cohort_start, AccountORM.created_at < cohort_end)
                .subquery()
            )
            cohort_total = self._db.query(func.count()).select_from(cohort_ids).scalar() or 0
            if cohort_total == 0:
                points.append(RetentionPoint(day=day, rate=0.0))
                continue

            returned = (
                self._db.query(func.count(distinct(EventORM.account_id)))
                .filter(
                    EventORM.account_id.in_(self._db.query(cohort_ids)),
                    EventORM.event_type == "app_open",
                    EventORM.occurred_at >= target_start,
                    EventORM.occurred_at < target_end,
                )
                .scalar() or 0
            )
            points.append(RetentionPoint(day=day, rate=round(returned / cohort_total, 4)))

        return points

    def _calc_activation_rate(self, total_users: int) -> float | None:
        """Activation Rate: core_start 이벤트가 있는 계정 / 전체 계정."""
        if total_users == 0:
            return None
        activated = (
            self._db.query(func.count(distinct(EventORM.account_id)))
            .filter(EventORM.event_type == "core_start")
            .scalar() or 0
        )
        return round(activated / total_users, 4)
