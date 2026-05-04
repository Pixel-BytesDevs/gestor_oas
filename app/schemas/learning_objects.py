from pydantic import BaseModel
from datetime import datetime
from typing import List, Optional, Any


class TypeBase(BaseModel):
    type: str


class TypeCreate(TypeBase):
    pass


class TypeResponse(TypeBase):
    id: int

    class Config:
        from_attributes = True


class LevelBase(BaseModel):
    level: str


class LevelCreate(LevelBase):
    pass


class LevelResponse(LevelBase):
    id: int

    class Config:
        from_attributes = True


class LearningStyleBase(BaseModel):
    stype: str


class LearningStyleCreate(LearningStyleBase):
    pass


class LearningStyleResponse(LearningStyleBase):
    id: int

    class Config:
        from_attributes = True


class TopicBase(BaseModel):
    nombre: str


class TopicCreate(TopicBase):
    pass


class TopicResponse(TopicBase):
    id: int

    class Config:
        from_attributes = True


class LOComponentBase(BaseModel):
    component_type: str
    file_name: str
    file_size: int
    file_extension: str
    estimated_duration: Optional[int] = None


class LOComponentCreate(LOComponentBase):
    pass


class LOComponentResponse(LOComponentBase):
    id: int
    idObject: int
    idType: int
    s3_bucket: str
    s3_key: str
    last_modified: datetime

    class Config:
        from_attributes = True


class LearningObjectBase(BaseModel):
    title: str
    author: Optional[str] = None
    idType: int
    idLevel: int
    idStyle: int
    idTopic: int
    ge_objective: Optional[str] = None  #NUEVO
    objectives: Optional[Any] = None #NUEVO
    approach: Optional[str] = None
    interactive_data: Optional[Any] = None
    estimated_duration: Optional[int] = None


class LearningObjectCreate(LearningObjectBase):
    pass


class LearningObjectResponse(LearningObjectBase):
    idObject: int
    s3_bucket: str
    s3_key: str
    file_name: str
    file_size: int
    file_extension: str
    last_modified: datetime
    components: List[LOComponentResponse] = []

    class Config:
        from_attributes = True