import logging
from typing import Optional, List
import json

from services.mongo_service import (
    QueryParams,
    QueryResult,
    query_collection,
    list_collections,
    get_collection_fields,
    get_collection_stats,
    create_index,
    get_collection_indexes,
    aggregate_collection
)

# Set up logging
logger = logging.getLogger(__name__)


class MongoHandler:
    """Handler class for MongoDB operations"""

    @staticmethod
    async def handle_list_collections() -> List[str]:
        """Handle listing all available collections in MongoDB"""
        try:
            collections = await list_collections()
            return collections
        except Exception as e:
            logger.error(f"❌ Error listing collections: {e}")
            raise Exception(f"Failed to list collections: {str(e)}")

    @staticmethod
    async def handle_get_collection_fields(collection_name: str) -> List[str]:
        """Handle getting all fields for a specific collection"""
        try:
            fields = await get_collection_fields(collection_name)
            if not fields:
                raise ValueError(f"Collection '{collection_name}' not found or empty")
            return fields
        except Exception as e:
            logger.error(f"❌ Error getting fields for collection {collection_name}: {e}")
            if isinstance(e, ValueError):
                raise e
            raise Exception(f"Failed to get collection fields: {str(e)}")

    @staticmethod
    async def handle_get_collection_stats(collection_name: str) -> dict:
        """Handle getting statistics for a specific collection"""
        try:
            stats = await get_collection_stats(collection_name)
            return stats
        except Exception as e:
            logger.error(f"❌ Error getting stats for collection {collection_name}: {e}")
            raise Exception(f"Failed to get collection stats: {str(e)}")

    @staticmethod
    async def handle_query_collection(
        collection_name: str,
        page: int = 1,
        limit: int = 10,
        search: Optional[str] = None,
        search_columns: Optional[str] = None,
        filters: Optional[str] = None,
        sort_by: Optional[str] = None,
        sort_order: str = "asc"
    ) -> QueryResult:
        """Handle querying a MongoDB collection with pagination, search, filtering, and sorting"""
        try:
            # Parse search columns
            search_columns_list = None
            if search_columns:
                search_columns_list = [col.strip() for col in search_columns.split(',')]

            # Parse filters
            filters_dict = None
            if filters:
                try:
                    filters_dict = json.loads(filters)
                except json.JSONDecodeError:
                    raise ValueError("Invalid JSON format for filters parameter")

            # Create query parameters
            query_params = QueryParams(
                page=page,
                limit=limit,
                search=search,
                search_columns=search_columns_list,
                filters=filters_dict,
                sort_by=sort_by,
                sort_order=sort_order
            )

            # Execute query
            result = await query_collection(collection_name, query_params)
            return result

        except ValueError as e:
            logger.error(f"❌ Validation error for collection {collection_name}: {e}")
            raise e
        except Exception as e:
            logger.error(f"❌ Error querying collection {collection_name}: {e}")
            raise Exception(f"Failed to query collection: {str(e)}")

    @staticmethod
    async def handle_query_collection_post(
        collection_name: str,
        query_params: QueryParams
    ) -> QueryResult:
        """Handle querying a MongoDB collection using POST method with request body"""
        try:
            result = await query_collection(collection_name, query_params)
            return result
        except ValueError as e:
            logger.error(f"❌ Validation error for collection {collection_name}: {e}")
            raise e
        except Exception as e:
            logger.error(f"❌ Error querying collection {collection_name}: {e}")
            raise Exception(f"Failed to query collection: {str(e)}")

    @staticmethod
    async def handle_get_collection_indexes(collection_name: str) -> dict:
        """Handle getting all indexes for a specific collection"""
        try:
            indexes = await get_collection_indexes(collection_name)
            return indexes
        except Exception as e:
            logger.error(f"❌ Error getting indexes for collection {collection_name}: {e}")
            raise Exception(f"Failed to get collection indexes: {str(e)}")

    @staticmethod
    async def handle_create_index(
        collection_name: str,
        field: str,
        index_type: str = "ascending"
    ) -> dict:
        """Handle creating an index on a field in a collection"""
        try:
            success = await create_index(collection_name, field, index_type)
            if success:
                return {
                    "message": f"Index created successfully on field '{field}' in collection '{collection_name}'"
                }
            else:
                raise Exception("Failed to create index")
        except Exception as e:
            logger.error(f"❌ Error creating index: {e}")
            raise Exception(f"Failed to create index: {str(e)}")

    @staticmethod
    async def handle_aggregate_collection(
        collection_name: str,
        pipeline: List[dict]
    ) -> dict:
        """Handle executing aggregation pipeline on a collection"""
        try:
            result = await aggregate_collection(collection_name, pipeline)
            return {
                "collection_name": collection_name,
                "pipeline_stages": len(pipeline),
                "result_count": len(result),
                "data": result
            }
        except Exception as e:
            logger.error(f"❌ Error executing aggregation: {e}")
            raise Exception(f"Failed to execute aggregation: {str(e)}")