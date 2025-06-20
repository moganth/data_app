import motor.motor_asyncio
import ssl
import asyncpg

from config import (
    MONGO_URI, MONGO_DB,
    SUPABASE_DB_HOST, SUPABASE_DB_PORT,
    SUPABASE_DB_NAME, SUPABASE_DB_USER, SUPABASE_DB_PASSWORD
)

mongo_client = motor.motor_asyncio.AsyncIOMotorClient(MONGO_URI)
mongo_db = mongo_client[MONGO_DB]

async def get_supabase_connection():
    ssl_context = ssl.create_default_context()
    ssl_context.check_hostname = False
    ssl_context.verify_mode = ssl.CERT_NONE

    return await asyncpg.connect(
        user=SUPABASE_DB_USER,
        password=SUPABASE_DB_PASSWORD,
        database=SUPABASE_DB_NAME,
        host=SUPABASE_DB_HOST,
        port=int(SUPABASE_DB_PORT) if SUPABASE_DB_PORT else 5432,
        ssl=ssl_context,
        command_timeout=60,
        server_settings={
            'jit': 'off'
        }
    )
