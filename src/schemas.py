from typing import Literal

from pydantic import BaseModel, Field


class TriageRequest(BaseModel):
    text: str = Field(min_length=1, max_length=2000)


class TriageResult(BaseModel):
    category: Literal["billing", "bug", "feature", "other"]
    urgency: Literal["low", "normal", "high"]
    confidence: float = Field(ge=0.0, le=1.0)
    reason: str