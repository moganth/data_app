import logging
from typing import Optional
import json

from services.supabase_service import (
    QueryParams,
    QueryResult,
    query_table,
)

logger = logging.getLogger(__name__)


class SupabaseHandler:

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

        try:

            search_columns_list = None
            if search_columns:
                search_columns_list = [col.strip() for col in search_columns.split(',')]

            filters_dict = None
            if filters:
                try:
                    filters_dict = json.loads(filters)
                except json.JSONDecodeError:
                    raise ValueError("Invalid JSON format for filters parameter")

            query_params = QueryParams(
                page=page,
                limit=limit,
                search=search,
                search_columns=search_columns_list,
                filters=filters_dict,
                sort_by=sort_by,
                sort_order=sort_order
            )

            result = await query_table(table_name, query_params)
            return result

        except ValueError as e:
            logger.error(f"Validation error for table {table_name}: {e}")
            raise e
        except Exception as e:
            logger.error(f"Error querying table {table_name}: {e}")
            raise Exception(f"Failed to query table: {str(e)}")

    @staticmethod
    async def handle_query_table_post(
        table_name: str,
        query_params: QueryParams
    ) -> QueryResult:

        try:
            result = await query_table(table_name, query_params)
            return result
        except ValueError as e:
            logger.error(f" Validation error for table {table_name}: {e}")
            raise e
        except Exception as e:
            logger.error(f" Error querying table {table_name}: {e}")
            raise Exception(f"Failed to query table: {str(e)}")