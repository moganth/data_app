from typing import Optional
from fastapi import APIRouter, Query, HTTPException, Body

from handlers.supabase_handler import SupabaseHandler
from services.supabase_service import QueryParams, QueryResult

router = APIRouter()


@router.get("/tables/{table_name}/query", response_model=QueryResult)
async def query_table_endpoint(
        table_name: str,

        page: int = Query(1, ge=1, description="Page number (starts from 1)"),
        limit: int = Query(10, ge=1, le=1000, description="Number of records per page (max 1000)"),

        search: Optional[str] = Query(None, description="Search term to look for across specified columns"),
        search_columns: Optional[str] = Query(None, description="Comma-separated list of columns to search in"),

        filters: Optional[str] = Query(None,
                                       description="JSON string of filters e.g. {'age': {'gte': 18}, 'status': 'active'}"),

        sort_by: Optional[str] = Query(None, description="Column name to sort by"),
        sort_order: str = Query("asc", pattern="^(asc|desc)$", description="Sort order: asc or desc"),
):
    try:
        return await SupabaseHandler.handle_query_table(
            table_name=table_name,
            page=page,
            limit=limit,
            search=search,
            search_columns=search_columns,
            filters=filters,
            sort_by=sort_by,
            sort_order=sort_order
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/tables/{table_name}/query-json", response_model=QueryResult)
async def query_table_json_endpoint(
        table_name: str,
        query_params: QueryParams = Body(
            ...,
            example={
                "page": 1,
                "limit": 10,
                "search": "example search",
                "search_columns": ["column1", "column2"],
                "filters": {
                    "age": {"gte": 18, "lt": 65},
                    "status": "active",
                    "category": {"in": ["A", "B", "C"]},
                    "name": {"contains": "john"}
                },
                "sort_by": "created_at",
                "sort_order": "desc"
            }
        )
):
    """
    **Filter Operations Supported:**
    - `gte`: Greater than or equal
    - `gt`: Greater than
    - `lte`: Less than or equal
    - `lt`: Less than
    - `eq`: Equal to
    - `ne`: Not equal to
    - `in`: Value in list
    - `contains`: String contains (case-insensitive)
    - `startswith`: String starts with
    - `endswith`: String ends with

    Table_Name: books

    **Input:**
    ```json
    {
        "page": 1,
        "limit": 10,
        "search": "",
        "search_columns": ["title", "author"],
        "filters": {
            "published_year": { "gte": 2010 },
            "category": { "in": ["fiction", "science"] },
            "title": { "contains": "space" },
            "status": "available"
            },
        "sort_by": "published_year",
        "sort_order": "desc"
    }
    ```
    """
    try:
        return await SupabaseHandler.handle_query_table_post(table_name, query_params)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))