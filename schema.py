from typing import List
from pydantic import BaseModel, Field

class ReviewResult(BaseModel):
    quality_score: int = Field(ge=1, le=10, description="Overall research quality score from 1 to 10.")
    is_approved: bool = Field(description="True if the draft is factually supported by the sources.")
    feedback: str = Field(description="Specific issues found and instructions on how to fix them.")
    followup_queries: List[str] = Field(default_factory=list, description="Optional queries to help gather missing information.")