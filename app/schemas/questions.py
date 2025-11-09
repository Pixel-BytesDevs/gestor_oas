from pydantic import BaseModel
from datetime import datetime
from typing import List, Optional


class QuestionAlternativeBase(BaseModel):
    alternative_text: str
    is_correct: bool


class QuestionAlternativeCreate(QuestionAlternativeBase):
    pass


class QuestionAlternativeResponse(QuestionAlternativeBase):
    id: int
    question_id: int

    class Config:
        from_attributes = True


class QuestionBase(BaseModel):
    question_text: str
    id_topic: int
    difficulty_level: Optional[str] = None


class QuestionCreate(QuestionBase):
    alternatives: List[QuestionAlternativeCreate]


class QuestionResponse(QuestionBase):
    id: int
    created_at: datetime
    updated_at: Optional[datetime] = None
    alternatives: List[QuestionAlternativeResponse] = []

    class Config:
        from_attributes = True