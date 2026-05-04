from sqlalchemy import Column, Integer, String, Text, Boolean, ForeignKey, DateTime, BigInteger, JSON
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

Base = declarative_base()


class Type(Base):
    __tablename__ = "types"

    id = Column(Integer, primary_key=True, index=True)
    type = Column(String(50), unique=True, nullable=False)


class Level(Base):
    __tablename__ = "levels"

    id = Column(Integer, primary_key=True, index=True)
    level = Column(String(50), unique=True, nullable=False)


class LearningStyle(Base):
    __tablename__ = "learning_styles"

    id = Column(Integer, primary_key=True, index=True)
    stype = Column(String(50), unique=True, nullable=False)


class Topic(Base):
    __tablename__ = "topics"

    id = Column(Integer, primary_key=True, index=True)
    nombre = Column(String(100), nullable=False)


class LearningObject(Base):
    __tablename__ = "learning_objects"

    idObject = Column(Integer, primary_key=True, index=True)
    idType = Column(Integer, ForeignKey("types.id"))
    idLevel = Column(Integer, ForeignKey("levels.id"))
    idStyle = Column(Integer, ForeignKey("learning_styles.id"))
    idTopic = Column(Integer, ForeignKey("topics.id"))
    title = Column(String(200), nullable=False)
    author = Column(String(100))
    ge_objective = Column(Text, nullable=True)
    objectives = Column(JSON, nullable=True)
    approach = Column(Text, nullable=True)
    interactive_data = Column(JSON, nullable=True)
    s3_bucket = Column(String(100))
    s3_key = Column(String(500))
    s3_url = Column(String(1000))
    file_name = Column(String(200))
    file_size = Column(BigInteger)
    file_extension = Column(String(10))
    estimated_duration = Column(Integer)  # en minutos
    last_modified = Column(DateTime(timezone=True), server_default=func.now())

    # Relaciones
    type = relationship("Type")
    level = relationship("Level")
    style = relationship("LearningStyle")
    topic = relationship("Topic")
    components = relationship("LOComponent", back_populates="learning_object")


class LOComponent(Base):
    __tablename__ = "lo_components"

    id = Column(Integer, primary_key=True, index=True)
    idObject = Column(Integer, ForeignKey("learning_objects.idObject"))
    idType = Column(Integer, ForeignKey("types.id"))
    component_type = Column(String(50))  # 'objetivos', 'teoria', 'ejercicios', 'ejemplos'
    s3_bucket = Column(String(100))
    s3_key = Column(String(500))
    s3_url = Column(String(1000))
    file_name = Column(String(200))
    file_size = Column(BigInteger)
    file_extension = Column(String(10))
    estimated_duration = Column(Integer)
    last_modified = Column(DateTime(timezone=True), server_default=func.now())

    # Relaciones
    learning_object = relationship("LearningObject", back_populates="components")
    type = relationship("Type")


class Question(Base):
    __tablename__ = "questions"

    id = Column(Integer, primary_key=True, index=True)
    question_text = Column(Text, nullable=False)
    id_topic = Column(Integer, ForeignKey("topics.id"))
    difficulty_level = Column(String(50))
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relaciones
    topic = relationship("Topic")
    alternatives = relationship("QuestionAlternative", back_populates="question")


class QuestionAlternative(Base):
    __tablename__ = "question_alternatives"

    id = Column(Integer, primary_key=True, index=True)
    question_id = Column(Integer, ForeignKey("questions.id"))
    alternative_text = Column(Text, nullable=False)
    is_correct = Column(Boolean, default=False)

    # Relaciones
    question = relationship("Question", back_populates="alternatives")