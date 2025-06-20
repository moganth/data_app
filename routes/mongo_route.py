from typing import Optional, List
from fastapi import APIRouter, Query, HTTPException

from handlers.mongo_handler import MongoHandler
from services.mongo_service import QueryParams, QueryResult

router = APIRouter()


@router.get("/collections", response_model=List[str])
async def get_collections():
    """List all available collections in MongoDB"""
    try:
        return await MongoHandler.handle_list_collections()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/collections/{collection_name}/fields", response_model=List[str])
async def get_collection_fields_endpoint(collection_name: str):
    """Get all fields for a specific collection"""
    try:
        return await MongoHandler.handle_get_collection_fields(collection_name)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/collections/{collection_name}/stats")
async def get_collection_stats_endpoint(collection_name: str):
    """Get statistics for a specific collection"""
    try:
        return await MongoHandler.handle_get_collection_stats(collection_name)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/collections/{collection_name}/query", response_model=QueryResult)
async def query_collection_endpoint(
        collection_name: str,
        # Pagination
        page: int = Query(1, ge=1, description="Page number (starts from 1)"),
        limit: int = Query(10, ge=1, le=1000, description="Number of records per page (max 1000)"),

        # Search
        search: Optional[str] = Query(None, description="Search term to look for across specified fields"),
        search_columns: Optional[str] = Query(None, description="Comma-separated list of fields to search in"),

        # Filters (as query parameters)
        filters: Optional[str] = Query(None,
                                       description="JSON string of filters e.g. {'age': {'gte': 18}, 'status': 'active'}"),

        # Sorting
        sort_by: Optional[str] = Query(None, description="Field name to sort by"),
        sort_order: str = Query("asc", pattern="^(asc|desc)$", description="Sort order: asc or desc"),
):
    """Query a MongoDB collection with pagination, search, filtering, and sorting capabilities."""
    try:
        return await MongoHandler.handle_query_collection(
            collection_name=collection_name,
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


@router.post("/collections/{collection_name}/query", response_model=QueryResult)
async def query_collection_post_endpoint(
        collection_name: str,
        query_params: QueryParams
):
    """Query a MongoDB collection using POST method with request body for complex filters."""
    try:
        return await MongoHandler.handle_query_collection_post(collection_name, query_params)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ================================
# MONGODB ADVANCED ENDPOINTS
# ================================

@router.get("/collections/{collection_name}/indexes")
async def get_collection_indexes_endpoint(collection_name: str):
    """Get all indexes for a specific collection"""
    try:
        return await MongoHandler.handle_get_collection_indexes(collection_name)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/collections/{collection_name}/indexes")
async def create_index_endpoint(
        collection_name: str,
        field: str = Query(..., description="Field name to create index on"),
        index_type: str = Query("ascending", pattern="^(ascending|descending)$", description="Index type")
):
    """Create an index on a field in a collection"""
    try:
        return await MongoHandler.handle_create_index(collection_name, field, index_type)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/collections/{collection_name}/aggregate")
async def aggregate_collection_endpoint(
        collection_name: str,
        pipeline: List[dict]
):
    """Execute aggregation pipeline on a collection"""
    try:
        return await MongoHandler.handle_aggregate_collection(collection_name, pipeline)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))