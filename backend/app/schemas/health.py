from typing import Literal

from pydantic import BaseModel


class HealthRead(BaseModel):
    status: Literal["OK", "error"]
    database: Literal["OK", "unreachable"]
