import pandas as pd
from fastapi import UploadFile
import io


async def parse_file(file: UploadFile) -> pd.DataFrame:
    content = await file.read()
    if file.filename.endswith('.csv'):
        df = pd.read_csv(io.BytesIO(content))
    elif file.filename.endswith(('.xls', '.xlsx')):
        df = pd.read_excel(io.BytesIO(content))
    else:
        raise ValueError("Unsupported file format")

    return df
