from pymongo import MongoClient
from pymongo.errors import ConnectionFailure
from app.core.config import settings

client = None
db = None

def connect_to_mongo():
    global client, db
    try:
        client = MongoClient(settings.MONGO_DB_URL)
        db = client.get_database()
        client.admin.command('ismaster')
        print(f"Group Service: Connected to MongoDB at {settings.MONGO_DB_URL}")
    except ConnectionFailure as e:
        print(f"Group Service: Could not connect to MongoDB: {e}")
        exit(1)

def close_mongo_connection():
    global client
    if client:
        client.close()
        print("Group Service: MongoDB connection closed.")

def get_database():
    return db