from typing import Literal, Optional

from pydantic import BaseModel

EventType = Literal["visit", "app_open", "core_start", "core_complete"]


class RecordEventRequest(BaseModel):
    event_type: EventType
    campaign: Optional[str] = None
