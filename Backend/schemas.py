from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime

# User Schemas
class UserCreate(BaseModel):
    username: str = Field(..., min_length=3, max_length=50)
    password: str = Field(..., min_length=6)

class UserResponse(BaseModel):
    id: int
    username: str
    created_at: datetime

    class Config:
        from_attributes = True

# Token Schemas
class Token(BaseModel):
    access_token: str
    token_type: str

class TokenData(BaseModel):
    username: Optional[str] = None
    user_id: Optional[int] = None

# Tag Schemas
class TagCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=50)
    description: Optional[str] = Field(None, max_length=200)

class TagResponse(BaseModel):
    id: int
    name: str
    description: Optional[str]
    is_system: bool

    class Config:
        from_attributes = True

# Question Schemas
class QuestionCreate(BaseModel):
    text: str = Field(..., min_length=5, max_length=2000)
    # Optional list of tags. If not provided or empty, we will auto-tag.
    tags: Optional[List[str]] = None

class QuestionResponse(BaseModel):
    id: int
    text: str
    user_id: int
    username: str
    created_at: datetime
    tags: List[TagResponse]

    class Config:
        from_attributes = True

# Match result in Similarity Search
class SimilarityResult(BaseModel):
    id: int
    text: str
    similarity_score: float
    user_id: int
    username: str
    created_at: datetime
    tags: List[TagResponse]

# Tag analysis item
class TagAnalysisItem(BaseModel):
    tag_id: int
    name: str
    similarity_score: float

# Pre-submit analysis response
class QuestionAnalyzeResponse(BaseModel):
    text: str
    suggested_tags: List[TagAnalysisItem]
    similar_questions: List[SimilarityResult]
