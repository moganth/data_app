from typing import Dict, List, Any, Optional
from pydantic import BaseModel

class QueryResult(BaseModel):
    data: List[Dict[str, Any]]
    total_count: int
    page: int
    limit: int
    total_pages: int
    has_next: bool
    has_previous: bool

class QueryParams(BaseModel):
    page: int = 1
    limit: int = 10

    search: Optional[str] = None
    search_columns: Optional[List[str]] = None

    filters: Optional[Dict[str, Any]] = None

    sort_by: Optional[str] = None
    sort_order: str = "asc"