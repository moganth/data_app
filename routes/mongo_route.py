from typing import Optional, List
from fastapi import APIRouter, Query, HTTPException, Body

from handlers.mongo_handler import MongoHandler
from services.mongo_service import QueryParams, QueryResult

router = APIRouter()


@router.get("/collections", response_model=List[str])
async def get_collections():
    try:
        return await MongoHandler.handle_list_collections()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/collections/{collection_name}/query", response_model=QueryResult)
async def query_collection_endpoint(
        collection_name: str,

        page: int = Query(1, ge=1, description="Page number (starts from 1)"),
        limit: int = Query(10, ge=1, le=1000, description="Number of records per page (max 1000)"),

        search: Optional[str] = Query(None, description="Search term to look for across specified fields"),
        search_columns: Optional[str] = Query(None, description="Comma-separated list of fields to search in"),

        filters: Optional[str] = Query(None,
                                       description="JSON string of filters e.g. {'age': {'gte': 18}, 'status': 'active'}"),

        sort_by: Optional[str] = Query(None, description="Field name to sort by"),
        sort_order: str = Query("asc", pattern="^(asc|desc)$", description="Sort order: asc or desc"),
):
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


@router.post("/collections/{collection_name}/query-json", response_model=QueryResult)
async def query_collection_json_endpoint(
        collection_name: str,
        query_params: QueryParams = Body(
            ...,
            example={
                "page": 1,
                "limit": 10,
                "search": "example search",
                "search_columns": ["field1", "field2"],
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
    Query a MongoDB collection using JSON payload with advanced filtering capabilities.

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

    Collection_Name: uploads

    **Example Filters:**
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
        return await MongoHandler.handle_query_collection_post(collection_name, query_params)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# MONGODB ADVANCED ENDPOINTS

@router.get("/collections/{collection_name}/indexes")
async def get_collection_indexes_endpoint(collection_name: str):
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
    try:
        return await MongoHandler.handle_create_index(collection_name, field, index_type)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/collections/{collection_name}/aggregate")
async def aggregate_collection_endpoint(
        collection_name: str,
        pipeline: List[dict]
):
    """
        Execute aggregation pipeline on a collection.

        Collection_Name: uploads

        **Example-1:**
        ```json
        [
            { "$sort": { "rating": -1 } },
            { "$limit": 5 },
            { "$project": { "_id": 0, "title": 1, "author": 1, "rating": 1 } }
        ]

        ```
        **Example-2:**
        ```json
        [
            {
                "$group": {
                "_id": "$language",
                "total_books": { "$sum": 1 }
                }
            },
            { "$sort": { "total_books": -1 } }
        ]
        ```
        """
    try:
        return await MongoHandler.handle_aggregate_collection(collection_name, pipeline)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))