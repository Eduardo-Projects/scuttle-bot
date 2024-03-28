import os
from pymongo import MongoClient
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

client = MongoClient(os.getenv("MONGO_DB_URI"))
db = client["league_discord_bot"]


async def add_summoner(name):
    summoner_collection = db.summoners
    summoner_document = {"name": name, "last_checked": 0}
    summoner_collection.insert_one(summoner_document)


async def get_summoners():
    return list(db.summoners.find({}, {"_id": 0, "name": 1}))
