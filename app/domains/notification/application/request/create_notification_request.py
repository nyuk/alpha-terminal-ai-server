from pydantic import BaseModel


class CreateNotificationRequest(BaseModel):
    user_id: int
    title: str
    body: str
