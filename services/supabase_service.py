import pandas as pd
import re
import asyncpg

from typing import Dict, List, Any, Tuple
from dotenv import load_dotenv
import logging

from config import (
    SUPABASE_DB_HOST,
    SUPABASE_DB_PORT,
    SUPABASE_DB_NAME,
    SUPABASE_DB_USER,
    SUPABASE_DB_PASSWORD
    #SUPABASE_SERVICE_ROLE_KEY
)
from utils.database_connections import get_supabase_connection as get_connection
from schemas.schema import QueryResult, QueryParams

load_dotenv()
logger = logging.getLogger(__name__)


def infer_pg_type(series: pd.Series):
    non_null_series = series.dropna()
    if len(non_null_series) == 0:
        return "TEXT"

    dtype = non_null_series.dtype

    if pd.api.types.is_integer_dtype(dtype):
        return "BIGINT"
    elif pd.api.types.is_float_dtype(dtype):
        return "DOUBLE PRECISION"
    elif pd.api.types.is_bool_dtype(dtype):
        return "BOOLEAN"
    elif pd.api.types.is_datetime64_any_dtype(dtype):
        return "TIMESTAMP"
    else:
        return "TEXT"


def sanitize_column_name(col_name: str) -> str:

    sanitized = re.sub(r'[^a-zA-Z0-9_]', '_', str(col_name))
    if sanitized[0].isdigit():
        sanitized = f"col_{sanitized}"
    return sanitized.lower()


async def test_connection():
    try:
        conn = await get_connection()
        await conn.close()
        logger.info("Supabase connection successful")
        return True
    except Exception as e:
        logger.error(f"Supabase connection failed: {e}")
        return False


async def create_table_and_insert(table_name: str, df: pd.DataFrame):

    table_name = sanitize_column_name(table_name)

    if df.empty:
        raise ValueError("DataFrame is empty")

    df.columns = [sanitize_column_name(col) for col in df.columns]
    column_defs = []
    for col in df.columns:
        pg_type = infer_pg_type(df[col])
        column_defs.append(f'"{col}" {pg_type}')

    create_stmt = f'''
    CREATE TABLE IF NOT EXISTS "{table_name}" (
        id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
        {', '.join(column_defs)},
        created_at TIMESTAMP DEFAULT NOW()
    );
    '''

    logger.info(f"Creating table: {table_name}")
    logger.info(f"Columns: {list(df.columns)}")

    conn = None
    try:
        conn = await get_connection()
        await conn.execute("CREATE EXTENSION IF NOT EXISTS \"uuid-ossp\";")

        await conn.execute(create_stmt)
        logger.info(f" Table '{table_name}' created successfully")

        records = df.to_dict(orient="records")

        if records:

            clean_records = []
            for record in records:
                clean_record = {}
                for key, value in record.items():
                    if pd.isna(value):
                        clean_record[key] = None
                    else:
                        clean_record[key] = value
                clean_records.append(clean_record)

            keys = list(clean_records[0].keys())
            placeholders = ", ".join(f"${i + 1}" for i in range(len(keys)))
            columns = ", ".join(f'"{k}"' for k in keys)

            insert_stmt = f'INSERT INTO "{table_name}" ({columns}) VALUES ({placeholders})'

            values_list = [tuple(record[key] for key in keys) for record in clean_records]

            await conn.executemany(insert_stmt, values_list)
            logger.info(f"Inserted {len(clean_records)} records into '{table_name}'")

    except asyncpg.exceptions.PostgresError as e:
        logger.error(f" PostgreSQL Error: {e}")
        raise
    except Exception as e:
        logger.error(f" Unexpected error: {e}")
        raise
    finally:
        if conn:
            await conn.close()
            logger.info(" Database connection closed")

def get_supabase_config():

    config = {
        "user": SUPABASE_DB_USER,
        "password": SUPABASE_DB_PASSWORD,
        "database": SUPABASE_DB_NAME,
        "host": SUPABASE_DB_HOST,
        "port":int(SUPABASE_DB_PORT) if SUPABASE_DB_PORT else 5432,
    }

    missing = [k for k, v in config.items() if not v]
    if missing:
        raise ValueError(f"Missing environment variables: {missing}")

    return config

async def get_table_columns(table_name: str) -> List[str]:
    conn = await get_connection()
    try:
        query = """
        SELECT column_name 
        FROM information_schema.columns 
        WHERE table_name = $1 
        AND table_schema = 'public'
        ORDER BY ordinal_position
        """
        rows = await conn.fetch(query, table_name)
        return [row['column_name'] for row in rows if row['column_name'] != 'id']
    finally:
        await conn.close()


async def list_tables() -> List[str]:
    conn = await get_connection()
    try:
        query = """
        SELECT table_name 
        FROM information_schema.tables 
        WHERE table_schema = 'public' 
        AND table_type = 'BASE TABLE'
        ORDER BY table_name
        """
        rows = await conn.fetch(query)
        return [row['table_name'] for row in rows]
    finally:
        await conn.close()


def build_where_clause(params: QueryParams, columns: List[str]) -> Tuple[str, List[Any]]:
    where_parts = []
    query_params = []
    param_counter = 1

    if params.search and params.search.strip():
        search_term = f"%{params.search.strip()}%"
        search_cols = params.search_columns if params.search_columns else columns

        valid_search_cols = [col for col in search_cols if col in columns]

        if valid_search_cols:
            search_conditions = []
            for col in valid_search_cols:
                search_conditions.append(f'CAST("{col}" AS TEXT) ILIKE ${param_counter}')
                query_params.append(search_term)
                param_counter += 1

            where_parts.append(f"({' OR '.join(search_conditions)})")

    if params.filters:
        for field, value in params.filters.items():
            if field not in columns:
                continue

            if isinstance(value, dict):
                for operator, filter_value in value.items():
                    if operator == "gte":
                        where_parts.append(f'"{field}" >= ${param_counter}')
                        query_params.append(filter_value)
                        param_counter += 1
                    elif operator == "gt":
                        where_parts.append(f'"{field}" > ${param_counter}')
                        query_params.append(filter_value)
                        param_counter += 1
                    elif operator == "lte":
                        where_parts.append(f'"{field}" <= ${param_counter}')
                        query_params.append(filter_value)
                        param_counter += 1
                    elif operator == "lt":
                        where_parts.append(f'"{field}" < ${param_counter}')
                        query_params.append(filter_value)
                        param_counter += 1
                    elif operator == "in" and isinstance(filter_value, list):
                        placeholders = [f"${param_counter + i}" for i in range(len(filter_value))]
                        where_parts.append(f'"{field}" IN ({", ".join(placeholders)})')
                        query_params.extend(filter_value)
                        param_counter += len(filter_value)
                    elif operator == "contains":
                        where_parts.append(f'CAST("{field}" AS TEXT) ILIKE ${param_counter}')
                        query_params.append(f"%{filter_value}%")
                        param_counter += 1
                    elif operator == "startswith":
                        where_parts.append(f'CAST("{field}" AS TEXT) ILIKE ${param_counter}')
                        query_params.append(f"{filter_value}%")
                        param_counter += 1
                    elif operator == "endswith":
                        where_parts.append(f'CAST("{field}" AS TEXT) ILIKE ${param_counter}')
                        query_params.append(f"%{filter_value}")
                        param_counter += 1
                    elif operator == "eq":
                        where_parts.append(f'"{field}" = ${param_counter}')
                        query_params.append(filter_value)
                        param_counter += 1
                    elif operator == "ne":
                        where_parts.append(f'"{field}" != ${param_counter}')
                        query_params.append(filter_value)
                        param_counter += 1
            else:
                where_parts.append(f'"{field}" = ${param_counter}')
                query_params.append(value)
                param_counter += 1

    where_clause = " AND ".join(where_parts) if where_parts else ""
    return where_clause, query_params


def build_order_clause(params: QueryParams, columns: List[str]) -> str:
    if not params.sort_by or params.sort_by not in columns:
        return 'ORDER BY "id"'

    order = "DESC" if params.sort_order.lower() == "desc" else "ASC"
    return f'ORDER BY "{params.sort_by}" {order}'


async def query_table(table_name: str, params: QueryParams) -> QueryResult:
    conn = await get_connection()

    try:
        columns = await get_table_columns(table_name)
        if not columns:
            raise ValueError(f"Table '{table_name}' not found or has no columns")

        where_clause, query_params = build_where_clause(params, columns)

        order_clause = build_order_clause(params, columns)

        count_query = f'SELECT COUNT(*) as total FROM "{table_name}"'
        if where_clause:
            count_query += f" WHERE {where_clause}"

        total_count = await conn.fetchval(count_query, *query_params)

        offset = (params.page - 1) * params.limit
        total_pages = (total_count + params.limit - 1) // params.limit

        main_query = f'''
        SELECT * FROM "{table_name}"
        {f"WHERE {where_clause}" if where_clause else ""}
        {order_clause}
        LIMIT ${len(query_params) + 1} OFFSET ${len(query_params) + 2}
        '''

        query_params.extend([params.limit, offset])

        rows = await conn.fetch(main_query, *query_params)

        data = [dict(row) for row in rows]

        for item in data:
            item.pop('id', None)

        return QueryResult(
            data=data,
            total_count=total_count,
            page=params.page,
            limit=params.limit,
            total_pages=total_pages,
            has_next=params.page < total_pages,
            has_previous=params.page > 1
        )

    finally:
        await conn.close()


async def get_table_stats(table_name: str) -> Dict[str, Any]:
    conn = await get_connection()

    try:
        stats_query = f'SELECT COUNT(*) as total_rows FROM "{table_name}"'
        total_rows = await conn.fetchval(stats_query)

        columns = await get_table_columns(table_name)

        sample_query = f'SELECT * FROM "{table_name}" LIMIT 100'
        sample_rows = await conn.fetch(sample_query)

        column_stats = {}
        if sample_rows:
            for col in columns:
                values = [row[col] for row in sample_rows if row[col] is not None]
                if values:
                    column_stats[col] = {
                        "non_null_count": len(values),
                        "data_type": type(values[0]).__name__,
                        "sample_values": list(set(values))[:10]
                    }

        return {
            "table_name": table_name,
            "total_rows": total_rows,
            "total_columns": len(columns),
            "columns": columns,
            "column_stats": column_stats
        }

    finally:
        await conn.close()