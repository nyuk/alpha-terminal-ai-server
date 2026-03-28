from datetime import datetime
from typing import List, Optional, Tuple

from sqlalchemy.orm import Session

from app.domains.market_video.application.usecase.market_video_repository_port import MarketVideoRepositoryPort
from app.domains.market_video.domain.entity.market_video import MarketVideo
from app.domains.market_video.infrastructure.mapper.market_video_mapper import MarketVideoMapper
from app.domains.market_video.infrastructure.orm.market_video_orm import MarketVideoORM


class MarketVideoRepositoryImpl(MarketVideoRepositoryPort):

    def __init__(self, db: Session):
        self._db = db

    def upsert_all(self, videos: List[MarketVideo]) -> List[MarketVideo]:
        """videoId 기준으로 insert/update. 오류가 발생한 영상은 건너뛴다."""
        saved: List[MarketVideo] = []

        for video in videos:
            try:
                existing: MarketVideoORM | None = (
                    self._db.query(MarketVideoORM)
                    .filter(MarketVideoORM.video_id == video.video_id)
                    .first()
                )
                if existing:
                    existing.title = video.title
                    existing.channel_name = video.channel_name
                    existing.published_at = video.published_at
                    existing.view_count = video.view_count
                    existing.thumbnail_url = video.thumbnail_url
                    existing.video_url = video.video_url
                    existing.updated_at = datetime.now()
                    saved.append(MarketVideoMapper.to_entity(existing))
                else:
                    orm = MarketVideoMapper.to_orm(video)
                    self._db.add(orm)
                    self._db.flush()
                    saved.append(MarketVideoMapper.to_entity(orm))
            except Exception:
                self._db.rollback()
                continue

        try:
            self._db.commit()
        except Exception:
            self._db.rollback()
            return []

        return saved

    def find_paginated(
        self,
        page: int,
        page_size: int,
        stock_name: Optional[str] = None,
    ) -> Tuple[List[MarketVideo], int]:
        query = self._db.query(MarketVideoORM).order_by(MarketVideoORM.published_at.desc())

        if stock_name:
            query = query.filter(MarketVideoORM.title.contains(stock_name))

        total = query.count()
        orms = query.offset((page - 1) * page_size).limit(page_size).all()
        return [MarketVideoMapper.to_entity(orm) for orm in orms], total
