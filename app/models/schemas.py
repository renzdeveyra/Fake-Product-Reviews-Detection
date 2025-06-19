from pydantic import BaseModel
from typing import List, Optional
class ReviewText(BaseModel):    text: str
class SentimentResponse(BaseModel):
    text: str
    sentiment: str
    score: float





