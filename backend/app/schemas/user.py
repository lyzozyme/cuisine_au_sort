import uuid

from app.schemas.common import ReadModel


class UserRead(ReadModel):
    id: uuid.UUID
    email: str
    display_name: str
