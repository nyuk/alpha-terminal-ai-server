from pydantic import BaseModel


class AccountSettingsResponse(BaseModel):
    is_watchlist_public: bool
