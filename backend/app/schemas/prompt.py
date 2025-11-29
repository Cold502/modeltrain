from datetime import datetime
from typing import Optional

from pydantic import BaseModel


class TestPromptBase(BaseModel):
    title: str
    content: str


class TestPromptCreate(TestPromptBase):
    pass


class TestPromptUpdate(BaseModel):
    title: Optional[str] = None
    content: Optional[str] = None


class TestPromptResponse(TestPromptBase):
    id: int
    created_by: Optional[int]
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
