import time
import logging
from typing import Optional, Dict, Any
from fastapi import UploadFile

from utils.file_parser import parse_file
from services.mongo_service import insert_many_mongo
from services.supabase_service import create_table_and_insert


logger = logging.getLogger(__name__)


class UploadHandler:

    @staticmethod
    def validate_file(file: UploadFile) -> None:
        if not file.filename:
            raise ValueError("No file uploaded")

        if not file.filename.endswith(('.csv', '.xlsx', '.xls')):
            raise ValueError("Only CSV and Excel files are supported")

    @staticmethod
    def validate_upload_options(mongo_only: bool, supabase_only: bool) -> None:
        if mongo_only and supabase_only:
            raise ValueError("Cannot specify both mongo_only and supabase_only")

    @staticmethod
    def generate_names(
        filename: str,
        table_name: Optional[str] = None,
        collection_name: Optional[str] = None
    ) -> tuple[str, str]:
        base_name = filename.split('.')[0].replace(" ", "_").replace("-", "_")
        timestamp = int(time.time())

        if not table_name:
            table_name = f"{base_name}_{timestamp}"

        if not collection_name:
            collection_name = f"{base_name}_{timestamp}"

        table_name = table_name.lower().replace(" ", "_").replace("-", "_")
        collection_name = collection_name.lower().replace(" ", "_").replace("-", "_")

        return table_name, collection_name

    @staticmethod
    async def handle_file_upload(
        file: UploadFile,
        table_name: Optional[str] = None,
        collection_name: Optional[str] = None,
        mongo_only: bool = False,
        supabase_only: bool = False
    ) -> Dict[str, Any]:

        try:
            UploadHandler.validate_file(file)
            UploadHandler.validate_upload_options(mongo_only, supabase_only)

            logger.info(f"Parsing file: {file.filename}")
            df = await parse_file(file)

            if df.empty:
                raise ValueError("Uploaded file is empty")

            logger.info(f"Parsed {len(df)} rows with {len(df.columns)} columns")

            table_name, collection_name = UploadHandler.generate_names(
                file.filename, table_name, collection_name
            )

            results = {
                "message": "Data processed successfully",
                "rows": len(df),
                "columns": len(df.columns),
                "table_name": table_name,
                "collection_name": collection_name,
                "mongo_success": False,
                "supabase_success": False
            }

            if not supabase_only:
                try:
                    logger.info("Inserting data to MongoDB...")
                    await insert_many_mongo(df.to_dict(orient="records"))
                    results["mongo_success"] = True
                    logger.info("MongoDB insertion successful")
                except Exception as e:
                    logger.error(f" MongoDB insertion failed: {e}")
                    results["mongo_error"] = str(e)

            if not mongo_only:
                try:
                    logger.info(" Inserting data to Supabase...")
                    await create_table_and_insert(table_name, df)
                    results["supabase_success"] = True
                    logger.info(" Supabase insertion successful")
                except Exception as e:
                    logger.error(f" Supabase insertion failed: {e}")
                    results["supabase_error"] = str(e)

            success_conditions = [
                (mongo_only and results["mongo_success"]),
                (supabase_only and results["supabase_success"]),
                (not mongo_only and not supabase_only and results["mongo_success"] and results["supabase_success"])
            ]

            if any(success_conditions):
                results["status"] = "success"
            elif results["mongo_success"] or results["supabase_success"]:
                results["status"] = "partial_success"
            else:
                results["status"] = "failure"
                raise Exception("Failed to insert data to specified databases")

            return results

        except ValueError as e:
            logger.error(f" Validation error: {e}")
            raise e
        except Exception as e:
            logger.error(f" Unexpected error: {e}")
            raise Exception(f"Internal server error: {str(e)}")