from pydantic import BaseModel
from typing import List

class PromptRequest(BaseModel):
    prompt: str

class PromptResponse(BaseModel):
    result: float
    random_integers: List[float]

