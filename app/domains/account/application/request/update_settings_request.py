from pydantic import BaseModel


class UpdateSettingsRequest(BaseModel):
    is_watchlist_public: bool
