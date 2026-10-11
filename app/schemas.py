from pydantic import BaseModel, EmailStr, Field, ConfigDict
from typing import Literal

class RecipientIn(BaseModel):
    name: str = Field(min_length=1, max_length=200)
    email: EmailStr

class JobCreate(BaseModel):
    event_name: str = Field(min_length=1, max_length=200)
    course_name: str = Field(min_length=1, max_length=200)
    issuer_name: str = Field(min_length=1, max_length=200)
    recipients: list[RecipientIn] = Field(min_length=1, max_length=1000)

class RecipientResult(BaseModel):
    id: int
    name: str
    email: str
    status: Literal["pending", "processing", "succeeded", "failed"]
    error: str | None = None
    certificate_url: str | None = None
    model_config = ConfigDict(from_attributes=True)

class JobResult(BaseModel):
    id: int
    event_name: str
    course_name: str
    issuer_name: str
    status: str
    total: int
    processed: int
    succeeded: int
    failed: int
    progress_percent: float
    recipients: list[RecipientResult]
