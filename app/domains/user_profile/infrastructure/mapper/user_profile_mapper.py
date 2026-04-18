import json
from datetime import datetime

from app.domains.user_profile.domain.entity.user_interaction import UserInteraction
from app.domains.user_profile.domain.entity.user_profile import UserProfile
from app.domains.user_profile.infrastructure.orm.user_interaction_orm import UserInteractionORM
from app.domains.user_profile.infrastructure.orm.user_profile_orm import UserProfileORM


class UserProfileMapper:
    @staticmethod
    def to_entity(orm: UserProfileORM) -> UserProfile:
        try:
            preferred_stocks = json.loads(orm.preferred_stocks) if orm.preferred_stocks else []
        except (json.JSONDecodeError, TypeError):
            preferred_stocks = []

        return UserProfile(
            id=orm.id,
            account_id=orm.account_id,
            preferred_stocks=preferred_stocks,
            interests_text=orm.interests_text or "",
        )

    @staticmethod
    def to_orm(entity: UserProfile) -> UserProfileORM:
        return UserProfileORM(
            account_id=entity.account_id,
            preferred_stocks=json.dumps(entity.preferred_stocks, ensure_ascii=False),
            interests_text=entity.interests_text,
        )


class UserInteractionMapper:
    @staticmethod
    def to_entity(orm: UserInteractionORM) -> UserInteraction:
        return UserInteraction(
            id=orm.id,
            account_id=orm.account_id,
            symbol=orm.symbol,
            interaction_type=orm.interaction_type,
            count=orm.count,
            content=orm.content,
            name=orm.name,
            market=orm.market,
            created_at=orm.created_at or datetime.now(),
        )

    @staticmethod
    def to_orm(entity: UserInteraction) -> UserInteractionORM:
        return UserInteractionORM(
            account_id=entity.account_id,
            symbol=entity.symbol,
            interaction_type=entity.interaction_type,
            count=entity.count,
            content=entity.content,
            name=entity.name,
            market=entity.market,
        )
