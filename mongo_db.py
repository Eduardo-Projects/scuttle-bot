import os
from pymongo import MongoClient
from dotenv import load_dotenv
import lol_api
import certifi

# Load environment variables from .env file
load_dotenv()
ca = certifi.where()


client = MongoClient(os.getenv("MONGO_DB_URI"), tlsCAFile=ca)
db = client["league_discord_bot"]


async def add_summoner(summoner_riot_id):
    puuid = await lol_api.fetch_summoner_puuid_by_riot_id(summoner_riot_id)
    if puuid:
        summoner_collection = db.summoners
        summoner_document = {
            "name": summoner_riot_id,
            "puuid": puuid,
            "last_checked": 0,
        }
        summoner_collection.insert_one(summoner_document)
        return True
    else:
        return False


async def get_summoners():
    return list(db.summoners.find({}, {"_id": 0, "name": 1, "puuid": 1}))
