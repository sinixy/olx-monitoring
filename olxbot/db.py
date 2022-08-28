import motor.motor_asyncio
from config import DB_HOST, DB_NAME
from datetime import datetime, timedelta
from asyncio import sleep


client = motor.motor_asyncio.AsyncIOMotorClient(DB_HOST)
db = client[DB_NAME]

async def start_daily_cleaning():
    last_update = datetime.now()
    while True:
        await sleep(3600)
        if datetime.now().day != last_update.day:
            await db.offers.delete_many({})
        last_update = datetime.now()