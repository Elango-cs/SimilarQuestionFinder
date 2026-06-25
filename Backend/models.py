from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey, Table
from sqlalchemy.orm import relationship
from datetime import datetime
from database import Base

# Many-to-many relationship association table between Questions and Tags
question_tag = Table(
    "question_tag",
    Base.metadata,
    Column("question_id", Integer, ForeignKey("questions.id", ondelete="CASCADE"), primary_key=True),
    Column("tag_id", Integer, ForeignKey("tags.id", ondelete="CASCADE"), primary_key=True)
)

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    questions = relationship("Question", back_populates="user", cascade="all, delete-orphan")

class Tag(Base):
    __tablename__ = "tags"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, index=True, nullable=False)
    description = Column(String, nullable=True)
    is_system = Column(Boolean, default=True)

    # Relationships
    questions = relationship("Question", secondary=question_tag, back_populates="tags")
    embedding = relationship("TagEmbedding", back_populates="tag", uselist=False, cascade="all, delete-orphan")

class Question(Base):
    __tablename__ = "questions"

    id = Column(Integer, primary_key=True, index=True)
    text = Column(String, nullable=False)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    user = relationship("User", back_populates="questions")
    tags = relationship("Tag", secondary=question_tag, back_populates="questions")
    embedding = relationship("QuestionEmbedding", back_populates="question", uselist=False, cascade="all, delete-orphan")

class QuestionEmbedding(Base):
    __tablename__ = "question_embeddings"

    question_id = Column(Integer, ForeignKey("questions.id", ondelete="CASCADE"), primary_key=True)
    embedding = Column(String, nullable=False)  # JSON-serialized list of floats

    # Relationships
    question = relationship("Question", back_populates="embedding")

class TagEmbedding(Base):
    __tablename__ = "tag_embeddings"

    tag_id = Column(Integer, ForeignKey("tags.id", ondelete="CASCADE"), primary_key=True)
    embedding = Column(String, nullable=False)  # JSON-serialized list of floats

    # Relationships
    tag = relationship("Tag", back_populates="embedding")
