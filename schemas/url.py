from pydantic import BaseModel, HttpUrl


class URLBase(BaseModel):
    original_url: HttpUrl
    short_code: str
    click_count: int = 0

class URLCreate(BaseModel):
    original_url: HttpUrl

class URL(URLBase):
    class Config:
        from_attributes = True