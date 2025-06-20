import logging
from typing import Optional, List
import json

from services.supabase_service import (
    QueryParams,
    QueryResult,
    query_table,
    list_tables,
    get_table_columns,
    get_table_stats
)

# Set up logging
logger = logging.getLogger(__name__)


class SupabaseHandler:
    """Handler class for Supabase operations"""

    @staticmethod
    async def handle_list_tables() -> List[str]:
        """Handle listing all available tables in Supabase"""
        try:
            tables = await list_tables()
            return tables
        except Exception as e:
            logger.error(f"❌ Error listing tables: {e}")
            raise Exception(f"Failed to list tables: {str(e)}")

    @staticmethod
    async def handle_get_table_columns(table_name: str) -> List[str]:
        """Handle getting all columns for a specific table"""
        try:
            columns = await get_table_columns(table_name)
            if not columns:
                raise ValueError(f"Table '{table_name}' not found")
            return columns
        except Exception as e:
            logger.error(f"❌ Error getting columns for table {table_name}: {e}")
            if isinstance(e, ValueError):
                raise e
            raise Exception(f"Failed to get table columns: {str(e)}")

    @staticmethod
    async def handle_get_table_stats(table_name: str) -> dict:
        """Handle getting statistics for a specific table"""
        try:
            stats = await get_table_stats(table_name)
            return stats
        except Exception as e:
            logger.error(f"❌ Error getting stats for table {table_name}: {e}")
            raise Exception(f"Failed to get table stats: {str(e)}")

    @staticmethod
    async def handle_query_table(
        table_name: str,
        page: int = 1,
        limit: int = 10,
        search: Optional[str] = None,
        search_columns: Optional[str] = None,
        filters: Optional[str] = None,
        sort_by: Optional[str] = None,
        sort_order: str = "asc"
    ) -> QueryResult:
        """Handle querying a Supabase table with pagination, search, filtering, and sorting"""
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
            result = await query_table(table_name, query_params)
            return result

        except ValueError as e:
            logger.error(f"❌ Validation error for table {table_name}: {e}")
            raise e
        except Exception as e:
            logger.error(f"❌ Error querying table {table_name}: {e}")
            raise Exception(f"Failed to query table: {str(e)}")

    @staticmethod
    async def handle_query_table_post(
        table_name: str,
        query_params: QueryParams
    ) -> QueryResult:
        """Handle querying a Supabase table using POST method with request body"""
        try:
            result = await query_table(table_name, query_params)
            return result
        except ValueError as e:
            logger.error(f"❌ Validation error for table {table_name}: {e}")
            raise e
        except Exception as e:
            logger.error(f"❌ Error querying table {table_name}: {e}")
            raise Exception(f"Failed to query table: {str(e)}")