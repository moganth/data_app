from fastapi import APIRouter, UploadFile, File, Query, HTTPException
from fastapi.responses import JSONResponse

from handlers.upload_handler import UploadHandler

router = APIRouter()


@router.post("/upload")
async def upload_file(
        file: UploadFile = File(...),
        table_name: str = Query(default=None, description="Optional Supabase table name"),
        collection_name: str = Query(default=None, description="Optional MongoDB collection name"),
        mongo_only: bool = Query(default=False, description="Upload to MongoDB only"),
        supabase_only: bool = Query(default=False, description="Upload to Supabase only")
):
    try:
        results = await UploadHandler.handle_file_upload(
            file=file,
            table_name=table_name,
            collection_name=collection_name,
            mongo_only=mongo_only,
            supabase_only=supabase_only
        )

        if results["status"] == "success":
            return results
        elif results["status"] == "partial_success":
            return JSONResponse(
                status_code=207,
                content=results
            )
        else:
            raise HTTPException(
                status_code=500,
                detail="Failed to insert data to specified databases"
            )

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))