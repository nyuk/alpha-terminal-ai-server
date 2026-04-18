from datetime import datetime
from typing import List, Optional

from sqlalchemy.orm import Session

from app.domains.user_profile.application.port.user_profile_repository_port import UserProfileRepositoryPort
from app.domains.user_profile.domain.entity.user_interaction import UserInteraction, InteractionType
from app.domains.user_profile.domain.entity.user_profile import UserProfile
from app.domains.user_profile.infrastructure.mapper.user_profile_mapper import UserInteractionMapper, UserProfileMapper
from app.domains.user_profile.infrastructure.orm.user_interaction_orm import UserInteractionORM
from app.domains.user_profile.infrastructure.orm.user_profile_orm import UserProfileORM


class UserProfileRepositoryImpl(UserProfileRepositoryPort):
    def __init__(self, db: Session):
        self._db = db

    def find_by_account_id(self, account_id: int) -> Optional[UserProfile]:
        orm = self._db.query(UserProfileORM).filter(
            UserProfileORM.account_id == account_id
        ).first()
        if orm is None:
            return None
        return UserProfileMapper.to_entity(orm)

    def save(self, profile: UserProfile) -> UserProfile:
        existing = self._db.query(UserProfileORM).filter(
            UserProfileORM.account_id == profile.account_id
        ).first()

        if existing:
            import json
            existing.preferred_stocks = json.dumps(profile.preferred_stocks, ensure_ascii=False)
            existing.interests_text = profile.interests_text
            self._db.commit()
            self._db.refresh(existing)
            return UserProfileMapper.to_entity(existing)

        orm = UserProfileMapper.to_orm(profile)
        self._db.add(orm)
        self._db.commit()
        self._db.refresh(orm)
        return UserProfileMapper.to_entity(orm)

    def find_interactions_by_account_id(self, account_id: int) -> List[UserInteraction]:
        orms = self._db.query(UserInteractionORM).filter(
            UserInteractionORM.account_id == account_id
        ).order_by(UserInteractionORM.created_at.desc()).all()
        return [UserInteractionMapper.to_entity(orm) for orm in orms]

    def save_interaction(self, interaction: UserInteraction) -> UserInteraction:
        orm = UserInteractionMapper.to_orm(interaction)
        self._db.add(orm)
        self._db.commit()
        self._db.refresh(orm)
        return UserInteractionMapper.to_entity(orm)

    def upsert_recently_viewed(self, interaction: UserInteraction) -> UserInteraction:
        existing = self._db.query(UserInteractionORM).filter(
            UserInteractionORM.account_id == interaction.account_id,
            UserInteractionORM.symbol == interaction.symbol,
            UserInteractionORM.interaction_type == InteractionType.CLICK,
        ).first()

        if existing:
            existing.name = interaction.name
            existing.market = interaction.market
            existing.created_at = datetime.now()
            self._db.commit()
            self._db.refresh(existing)
            return UserInteractionMapper.to_entity(existing)

        orm = UserInteractionMapper.to_orm(interaction)
        self._db.add(orm)
        self._db.commit()
        self._db.refresh(orm)
        return UserInteractionMapper.to_entity(orm)

    def enforce_max_recently_viewed(self, account_id: int, max_count: int) -> None:
        records = self._db.query(UserInteractionORM).filter(
            UserInteractionORM.account_id == account_id,
            UserInteractionORM.interaction_type == InteractionType.CLICK,
        ).order_by(UserInteractionORM.created_at.desc()).all()

        if len(records) > max_count:
            for record in records[max_count:]:
                self._db.delete(record)
            self._db.commit()
