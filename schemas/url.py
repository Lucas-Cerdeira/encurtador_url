from pydantic import BaseModel, HttpUrl, ConfigDict
from typing import Optional, Literal
from datetime import datetime
from enum import Enum


class SortByEnum(str, Enum):
    """Campos permitidos para ordenação."""
    created_at = "created_at"
    click_count = "click_count"
    original_url = "original_url"


class OrderEnum(str, Enum):
    """Direção da ordenação."""
    asc = "asc"
    desc = "desc"


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


class PaginationMetadata(BaseModel):
    """Metadados de paginação."""
    total: int
    page: int
    page_size: int
    total_pages: int
    has_next: bool
    has_previous: bool


class FilterMetadata(BaseModel):
    """Metadados dos filtros aplicados."""
    sort_by: str
    order: str
    search: Optional[str] = None
    min_clicks: Optional[int] = None
    max_clicks: Optional[int] = None
    created_after: Optional[datetime] = None
    created_before: Optional[datetime] = None


class URLListResponse(BaseModel):
    """Resposta da listagem de URLs com paginação e filtros."""
    total: int
    page: int
    page_size: int
    total_pages: int
    has_next: bool
    has_previous: bool
    filters: FilterMetadata
    urls: list[URLResponse]


class URL(URLBase):
    model_config = ConfigDict(from_attributes=True)