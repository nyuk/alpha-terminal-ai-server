from abc import ABC, abstractmethod
from typing import List, Optional

from app.domains.user_profile.domain.entity.user_interaction import UserInteraction
from app.domains.user_profile.domain.entity.user_profile import UserProfile


class UserProfileRepositoryPort(ABC):

    @abstractmethod
    def find_by_account_id(self, account_id: int) -> Optional[UserProfile]:
        pass

    @abstractmethod
    def save(self, profile: UserProfile) -> UserProfile:
        pass

    @abstractmethod
    def find_interactions_by_account_id(self, account_id: int) -> List[UserInteraction]:
        pass

    @abstractmethod
    def save_interaction(self, interaction: UserInteraction) -> UserInteraction:
        pass

    @abstractmethod
    def upsert_recently_viewed(self, interaction: UserInteraction) -> UserInteraction:
        pass

    @abstractmethod
    def enforce_max_recently_viewed(self, account_id: int, max_count: int) -> None:
        pass
