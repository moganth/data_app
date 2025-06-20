from typing import Optional, List
from fastapi import APIRouter, Query, HTTPException

from handlers.supabase_handler import SupabaseHandler
from services.supabase_service import QueryParams, QueryResult

router = APIRouter()


@router.get("/tables", response_model=List[str])
async def get_tables():
    """List all available tables in Supabase"""
    try:
        return await SupabaseHandler.handle_list_tables()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/tables/{table_name}/columns", response_model=List[str])
async def get_table_columns_endpoint(table_name: str):
    """Get all columns for a specific table"""
    try:
        return await SupabaseHandler.handle_get_table_columns(table_name)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/tables/{table_name}/stats")
async def get_table_stats_endpoint(table_name: str):
    """Get statistics for a specific table"""
    try:
        return await SupabaseHandler.handle_get_table_stats(table_name)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/tables/{table_name}/query", response_model=QueryResult)
async def query_table_endpoint(
        table_name: str,
        # Pagination
        page: int = Query(1, ge=1, description="Page number (starts from 1)"),
        limit: int = Query(10, ge=1, le=1000, description="Number of records per page (max 1000)"),

        # Search
        search: Optional[str] = Query(None, description="Search term to look for across specified columns"),
        search_columns: Optional[str] = Query(None, description="Comma-separated list of columns to search in"),

        # Filters (as query parameters)
        filters: Optional[str] = Query(None,
                                       description="JSON string of filters e.g. {'age': {'gte': 18}, 'status': 'active'}"),

        # Sorting
        sort_by: Optional[str] = Query(None, description="Column name to sort by"),
        sort_order: str = Query("asc", pattern="^(asc|desc)$", description="Sort order: asc or desc"),
):
    """Query a Supabase table with pagination, search, filtering, and sorting capabilities."""
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


@router.post("/tables/{table_name}/query", response_model=QueryResult)
async def query_table_post_endpoint(
        table_name: str,
        query_params: QueryParams
):
    """Query a Supabase table using POST method with request body for complex filters."""
    try:
        return await SupabaseHandler.handle_query_table_post(table_name, query_params)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))