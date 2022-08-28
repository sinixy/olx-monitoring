import os
from dotenv import load_dotenv

load_dotenv()


BOT_TOKEN = os.environ['BOT_TOKEN']
RECIEVER_ID = os.environ['RECIEVER_ID']
OFFER_RAW_FIELDS = ['id', 'title', 'url', 'created_time', 'description', 'params', 'photos']

DB_HOST = os.environ['DB_HOST']
DB_NAME = os.environ['DB_NAME']