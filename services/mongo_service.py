from typing import Dict, List, Any
import logging
import re
from bson import ObjectId
from pymongo import ASCENDING, DESCENDING

from config import MONGO_COLLECTION
from schemas.schema import QueryResult, QueryParams
from utils.database_connections import mongo_db as db

logger = logging.getLogger(__name__)

async def insert_many_mongo(data: list[dict]):
    if data:
        collection = db[MONGO_COLLECTION]
        await collection.insert_many(data)

async def get_collection(collection_name: str):
    return db[collection_name]


async def list_collections() -> List[str]:
    try:
        collections = await db.list_collection_names()
        return [col for col in collections if not col.startswith('system.')]
    except Exception as e:
        logger.error(f"Error listing collections: {e}")
        return []


async def get_collection_fields(collection_name: str) -> List[str]:
    try:
        collection = db[collection_name]
        pipeline = [
            {"$sample": {"size": 100}},  # Sample 100 documents
            {"$project": {"arrayofkeyvalue": {"$objectToArray": "$$ROOT"}}},
            {"$unwind": "$arrayofkeyvalue"},
            {"$group": {"_id": None, "allkeys": {"$addToSet": "$arrayofkeyvalue.k"}}}
        ]

        result = await collection.aggregate(pipeline).to_list(length=1)

        if result and result[0].get('allkeys'):
            fields = result[0]['allkeys']
            return [field for field in fields if not field.startswith('_')]
        else:
            doc = await collection.find_one()
            if doc:
                return [key for key in doc.keys() if not key.startswith('_')]
            return []

    except Exception as e:
        logger.error(f"Error getting collection fields: {e}")
        return []


def build_mongo_filter(params: QueryParams, fields: List[str]) -> Dict[str, Any]:
    mongo_filter = {}

    if params.search and params.search.strip():
        search_term = params.search.strip()
        search_cols = params.search_columns if params.search_columns else fields

        valid_search_cols = [col for col in search_cols if col in fields]

        if valid_search_cols:
            search_conditions = []
            for col in valid_search_cols:
                search_conditions.append({
                    col: {"$regex": re.escape(search_term), "$options": "i"}
                })

            mongo_filter["$or"] = search_conditions

    if params.filters:
        for field, value in params.filters.items():
            if field not in fields:
                continue

            if isinstance(value, dict):
                field_filter = {}
                for operator, filter_value in value.items():
                    if operator == "gte":
                        field_filter["$gte"] = filter_value
                    elif operator == "gt":
                        field_filter["$gt"] = filter_value
                    elif operator == "lte":
                        field_filter["$lte"] = filter_value
                    elif operator == "lt":
                        field_filter["$lt"] = filter_value
                    elif operator == "in" and isinstance(filter_value, list):
                        field_filter["$in"] = filter_value
                    elif operator == "contains":
                        field_filter["$regex"] = re.escape(str(filter_value))
                        field_filter["$options"] = "i"
                    elif operator == "startswith":
                        field_filter["$regex"] = f"^{re.escape(str(filter_value))}"
                        field_filter["$options"] = "i"
                    elif operator == "endswith":
                        field_filter["$regex"] = f"{re.escape(str(filter_value))}$"
                        field_filter["$options"] = "i"
                    elif operator == "eq":
                        field_filter["$eq"] = filter_value
                    elif operator == "ne":
                        field_filter["$ne"] = filter_value

                if field_filter:
                    mongo_filter[field] = field_filter
            else:

                mongo_filter[field] = value

    return mongo_filter


def build_mongo_sort(params: QueryParams, fields: List[str]) -> List[tuple]:
    if not params.sort_by or params.sort_by not in fields:
        return [("_id", ASCENDING)]

    direction = DESCENDING if params.sort_order.lower() == "desc" else ASCENDING
    return [(params.sort_by, direction)]


async def query_collection(collection_name: str, params: QueryParams) -> QueryResult:
    try:
        collection = db[collection_name]

        fields = await get_collection_fields(collection_name)
        if not fields:
            sample_doc = await collection.find_one()
            if sample_doc:
                fields = [key for key in sample_doc.keys() if not key.startswith('_')]
            else:
                raise ValueError(f"Collection '{collection_name}' is empty or not found")


        mongo_filter = build_mongo_filter(params, fields)

        sort_params = build_mongo_sort(params, fields)

        total_count = await collection.count_documents(mongo_filter)

        skip = (params.page - 1) * params.limit
        total_pages = (total_count + params.limit - 1) // params.limit

        cursor = collection.find(mongo_filter).sort(sort_params).skip(skip).limit(params.limit)
        documents = await cursor.to_list(length=params.limit)

        data = []
        for doc in documents:
            if '_id' in doc and isinstance(doc['_id'], ObjectId):
                doc.pop('_id')

            clean_doc = {}
            for key, value in doc.items():
                if isinstance(value, ObjectId):
                    clean_doc[key] = str(value)
                else:
                    clean_doc[key] = value
            data.append(clean_doc)

        return QueryResult(
            data=data,
            total_count=total_count,
            page=params.page,
            limit=params.limit,
            total_pages=total_pages,
            has_next=params.page < total_pages,
            has_previous=params.page > 1
        )

    except Exception as e:
        logger.error(f"Error querying collection '{collection_name}': {e}")
        raise


async def get_collection_stats(collection_name: str) -> Dict[str, Any]:

    try:
        collection = db[collection_name]

        total_docs = await collection.count_documents({})

        fields = await get_collection_fields(collection_name)

        sample_docs = await collection.find().limit(100).to_list(length=100)

        field_stats = {}
        if sample_docs:
            for field in fields:
                values = []
                for doc in sample_docs:
                    if field in doc and doc[field] is not None:
                        values.append(doc[field])

                if values:
                    sample_values = list(set(str(v) for v in values))[:10]

                    field_stats[field] = {
                        "non_null_count": len(values),
                        "data_type": type(values[0]).__name__,
                        "sample_values": sample_values
                    }

        stats_result = await db.command("collStats", collection_name)

        return {
            "collection_name": collection_name,
            "total_documents": total_docs,
            "total_fields": len(fields),
            "fields": fields,
            "field_stats": field_stats,
            "size_bytes": stats_result.get("size", 0),
            "storage_size_bytes": stats_result.get("storageSize", 0),
            "avg_doc_size": stats_result.get("avgObjSize", 0)
        }

    except Exception as e:
        logger.error(f"Error getting collection stats for '{collection_name}': {e}")
        raise


async def create_index(collection_name: str, field: str, index_type: str = "ascending") -> bool:
    try:
        collection = db[collection_name]

        direction = ASCENDING if index_type.lower() == "ascending" else DESCENDING

        await collection.create_index([(field, direction)])
        logger.info(f"Created {index_type} index on field '{field}' in collection '{collection_name}'")
        return True

    except Exception as e:
        logger.error(f"Error creating index: {e}")
        return False


async def get_collection_indexes(collection_name: str) -> List[Dict[str, Any]]:
    try:
        collection = db[collection_name]
        indexes = await collection.list_indexes().to_list(length=None)

        index_info = []
        for index in indexes:
            index_info.append({
                "name": index.get("name"),
                "key": index.get("key"),
                "unique": index.get("unique", False),
                "sparse": index.get("sparse", False)
            })

        return index_info

    except Exception as e:
        logger.error(f"Error getting indexes for collection '{collection_name}': {e}")
        return []


async def aggregate_collection(collection_name: str, pipeline: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    try:
        collection = db[collection_name]

        cursor = collection.aggregate(pipeline)
        results = await cursor.to_list(length=None)

        clean_results = []
        for result in results:
            clean_result = {}
            for key, value in result.items():
                if isinstance(value, ObjectId):
                    clean_result[key] = str(value)
                else:
                    clean_result[key] = value
            clean_results.append(clean_result)

        return clean_results

    except Exception as e:
        logger.error(f"Error executing aggregation on collection '{collection_name}': {e}")
        raise