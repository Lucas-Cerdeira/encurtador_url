from pydantic import BaseModel, HttpUrl, ConfigDict
from typing import Optional
from datetime import datetime


class URLBase(BaseModel):
    original_url: HttpUrl
    short_code: str
    click_count: int = 0

class URLCreate(BaseModel):
    original_url: HttpUrl

class URLUpdate(BaseModel):
    original_url: Optional[HttpUrl] = None

class URLResponse(BaseModel):
    id: int
    original_url: str
    short_code: str
    click_count: int
    created_at: datetime
    
    model_config = ConfigDict(from_attributes=True)

class URLListResponse(BaseModel):
    total: int
    page: int
    page_size: int
    urls: list[URLResponse]

class URL(URLBase):
    model_config = ConfigDict(from_attributes=True)