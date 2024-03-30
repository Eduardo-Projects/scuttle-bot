import os
from pymongo import MongoClient
from dotenv import load_dotenv
import lol_api
import certifi
from datetime import datetime

# Load environment variables from .env file
load_dotenv()
ca = certifi.where()


client = MongoClient(os.getenv("MONGO_DB_URI"), tlsCAFile=ca)
db = client["league_discord_bot"]


# Adds riot id and puuid to summoners list of the corresponding discord server in database
async def add_summoner(summoner_riot_id, guild_id):
    # check if riot user exists before inserting into db
    puuid = await lol_api.fetch_summoner_puuid_by_riot_id(summoner_riot_id)
    if puuid:
        collection = db.discord_servers
        # Update or insert  summoner riot id into the summoners array for the corresponding discord server
        result = collection.update_one(
            {"guild_id": guild_id},
            {"$addToSet": {"summoners": {"name": summoner_riot_id, "puuid": puuid}}},
            upsert=True,  # Creates a new document if one doesn't exist
        )
        if result.acknowledged:
            print(
                f"Document for summoner '{summoner_riot_id}' was successfully added to Guild with id {guild_id}"
            )
            return True
        else:
            print(
                f"Failed to insert document into MongoDB for summoner '{summoner_riot_id}'."
            )
    print(
        f"Failed to add summoner {summoner_riot_id} to database. Make sure this is a real riot account"
    )
    return False


# Retrieves a list of all summoners for given discord server
async def get_summoners(guild_id):
    # Retrieve the document for the server
    collection = db.discord_servers
    document = collection.find_one({"guild_id": guild_id})

    if document and "summoners" in document:
        summoners_list = document["summoners"]
        return summoners_list

    return None


# Creates and inserts a new discord server in database
async def add_guild(guild_name, guild_id):
    collection = db.discord_servers
    document = {"name": guild_name, "guild_id": guild_id, "date_added": datetime.now()}

    result = collection.insert_one(document)
    if result.acknowledged:
        print(
            f"Document for guild '{guild_name}' was successfully inserted into MongoDB with _id: {result.inserted_id}"
        )
    else:
        print(f"Failed to insert document into MongoDB for guild '{guild_name}'.")


# Sets the main channel for a discord server in database
# The main channel is where automatic messages will be sent
async def set_main_channel(guild_id, channel_id):
    collection = db.discord_servers
    result = collection.update_one(
        {"guild_id": guild_id},
        {"$set": {"main_channel_id": channel_id}},
        upsert=True,  # Creates a new document if one doesn't exist
    )

    # Check if the document was updated
    if result.modified_count > 0:
        print(f"\nMain channel for Guild with ID {guild_id} updated to {channel_id}.")
        return True
    else:
        print(
            "\nNo document matches the provided query, or the document already has the specified value for main_channel_id."
        )
    return False


# Retrieves the main_channel_id for a specific discord server
async def get_main_channel(guild_id):
    collection = db.discord_servers
    document = collection.find_one({"guild_id": guild_id})

    if document:
        main_channel_id = document.get("main_channel_id", None)
        return main_channel_id
    else:
        print(f"Document with Guild ID {guild_id} not found")
