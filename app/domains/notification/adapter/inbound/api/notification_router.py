from typing import List, Optional

from fastapi import APIRouter, Cookie, Depends, HTTPException
from sqlalchemy.orm import Session

from app.domains.auth.adapter.outbound.in_memory.redis_session_adapter import RedisSessionAdapter
from app.domains.notification.adapter.outbound.persistence.notification_repository_impl import NotificationRepositoryImpl
from app.domains.notification.application.request.create_notification_request import CreateNotificationRequest
from app.domains.notification.application.response.notification_response import NotificationResponse, UnreadCountResponse
from app.domains.notification.application.usecase.create_notification_usecase import CreateNotificationUseCase
from app.domains.notification.application.usecase.get_notifications_usecase import GetNotificationsUseCase
from app.domains.notification.application.usecase.get_unread_count_usecase import GetUnreadCountUseCase
from app.domains.notification.application.usecase.mark_read_usecase import MarkAllReadUseCase, MarkReadUseCase
from app.infrastructure.cache.redis_client import redis_client
from app.infrastructure.database.session import get_db

router = APIRouter(prefix="/notifications", tags=["notifications"])

_session_adapter = RedisSessionAdapter(redis_client)


def _resolve_account_id(
    account_id_cookie: Optional[str],
    user_token: Optional[str],
) -> Optional[int]:
    if account_id_cookie:
        try:
            return int(account_id_cookie)
        except ValueError:
            pass
    if user_token:
        session = _session_adapter.find_by_token(user_token)
        if session:
            try:
                return int(session.user_id)
            except ValueError:
                pass
    return None


@router.post("", response_model=NotificationResponse, status_code=201)
async def create_notification(
    request: CreateNotificationRequest,
    db: Session = Depends(get_db),
):
    repository = NotificationRepositoryImpl(db)
    usecase = CreateNotificationUseCase(repository)
    notification = usecase.execute(request)
    return NotificationResponse(
        id=notification.id,
        user_id=notification.user_id,
        title=notification.title,
        body=notification.body,
        is_read=notification.is_read,
        created_at=notification.created_at,
    )


@router.get("", response_model=List[NotificationResponse])
async def get_notifications(
    db: Session = Depends(get_db),
    account_id: Optional[str] = Cookie(default=None),
    user_token: Optional[str] = Cookie(default=None),
):
    aid = _resolve_account_id(account_id, user_token)
    if aid is None:
        raise HTTPException(status_code=401, detail="로그인이 필요합니다.")
    repository = NotificationRepositoryImpl(db)
    usecase = GetNotificationsUseCase(repository)
    notifications = usecase.execute(aid)
    return [
        NotificationResponse(
            id=n.id,
            user_id=n.user_id,
            title=n.title,
            body=n.body,
            is_read=n.is_read,
            created_at=n.created_at,
        )
        for n in notifications
    ]


@router.patch("/read-all")
async def mark_all_read(
    db: Session = Depends(get_db),
    account_id: Optional[str] = Cookie(default=None),
    user_token: Optional[str] = Cookie(default=None),
):
    aid = _resolve_account_id(account_id, user_token)
    if aid is None:
        raise HTTPException(status_code=401, detail="로그인이 필요합니다.")
    repository = NotificationRepositoryImpl(db)
    usecase = MarkAllReadUseCase(repository)
    count = usecase.execute(aid)
    return {"updated": count}


@router.patch("/{notification_id}/read")
async def mark_read(
    notification_id: int,
    db: Session = Depends(get_db),
    account_id: Optional[str] = Cookie(default=None),
    user_token: Optional[str] = Cookie(default=None),
):
    aid = _resolve_account_id(account_id, user_token)
    if aid is None:
        raise HTTPException(status_code=401, detail="로그인이 필요합니다.")
    repository = NotificationRepositoryImpl(db)
    usecase = MarkReadUseCase(repository)
    success = usecase.execute(notification_id)
    if not success:
        raise HTTPException(status_code=404, detail="알림을 찾을 수 없습니다.")
    return {"success": True}


@router.get("/unread-count", response_model=UnreadCountResponse)
async def get_unread_count(
    db: Session = Depends(get_db),
    account_id: Optional[str] = Cookie(default=None),
    user_token: Optional[str] = Cookie(default=None),
):
    aid = _resolve_account_id(account_id, user_token)
    if aid is None:
        raise HTTPException(status_code=401, detail="로그인이 필요합니다.")
    repository = NotificationRepositoryImpl(db)
    usecase = GetUnreadCountUseCase(repository)
    count = usecase.execute(aid)
    return UnreadCountResponse(unread_count=count)
