import os
from pymongo import MongoClient
from dotenv import load_dotenv
import lol_api
import certifi
from datetime import datetime, timedelta, timezone
import utils

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
                f"\nDocument for summoner '{summoner_riot_id}' was successfully added to Guild with id {guild_id}"
            )
            return True
        else:
            print(
                f"\nFailed to insert document into MongoDB for summoner '{summoner_riot_id}'."
            )
    print(
        f"\nFailed to add summoner {summoner_riot_id} to database. Make sure this is a real riot account"
    )
    return False


# Retrieves a list of all summoners for given discord server
async def get_summoners(guild_id):
    collection = db.discord_servers
    document = collection.find_one({"guild_id": guild_id})

    if document and "summoners" in document:
        summoners_list = document["summoners"]
        return summoners_list

    return None


# Creates and inserts a new discord server in database
async def add_guild(guild_name, guild_id):
    collection = db.discord_servers

    if collection.count_documents({"guild_id": guild_id}) == 0:
        document = {
            "name": guild_name,
            "guild_id": guild_id,
            "date_added": datetime.now(),
        }
        result = collection.insert_one(document)
        if result.acknowledged:
            print(
                f"Document for guild '{guild_name}' was successfully inserted into MongoDB with _id: {result.inserted_id}"
            )
        else:
            print(f"Failed to insert document into MongoDB for guild '{guild_name}'.")
    else:
        print(f"A document with the guild_id '{guild_id}' already exists.")


# Sets the main channel for a discord server in database
# The main channel is where automatic messages will be sent
async def set_main_channel(guild_id, channel_id):
    print(f"\nSetting main channel to {channel_id}")

    collection = db.discord_servers
    result = collection.update_one(
        {"guild_id": guild_id},
        {"$set": {"main_channel_id": channel_id}},
        upsert=True,  # Creates a new document if one doesn't exist
    )

    # Check if the document was updated
    if result.modified_count > 0:
        print(f"Main channel for Guild with ID {guild_id} updated to {channel_id}.")
        return True
    else:
        print(
            "No document matches the provided query, or the document already has the specified value for main_channel_id."
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


# Fetches stats for all matches played in the last {range} days
async def fetch_summoner_stats_by_day_range(summoner_puuid, range=7):
    print(f"\nFetching {range} day stats for {summoner_puuid}...")
    matches_data = await fetch_all_summoner_match_data_by_range(summoner_puuid, range)
    stats = utils.calculate_stats(summoner_puuid, matches_data)
    return stats


# Fetch weekly report of stats for all summoners in a discord server within certain range
# The report will display which summoner has the highest value for each stat
async def fetch_report_by_day_range(guild_id, range=7):
    print(f"\nFetching {range} day report for guild with id {guild_id}...")

    guild_data = db.discord_servers.find_one({"guild_id": guild_id})
    if guild_data:
        agg_stats = []
        summoners = await get_summoners(guild_id)

        if summoners:
            for summoner in summoners:
                puuid = summoner["puuid"]
                matches_data = await fetch_all_summoner_match_data_by_range(
                    summoner_puuid=puuid, range=range
                )
                stats = utils.calculate_stats(
                    summoner_puuid=puuid, matches_data=matches_data
                )
                weekly_stats_with_name = stats.copy()
                weekly_stats_with_name["Name"] = summoner["name"]
                agg_stats.append(weekly_stats_with_name)

            # Extract keys excluding 'Name'
            keys = [key for key in agg_stats[0] if key != "Name"]

            # Initialize a dictionary to store max values and corresponding names
            max_values = {key: {"value": float("-inf"), "Name": None} for key in keys}

            # Update max_values with the max value for each key and corresponding name
            for item in agg_stats:
                for key in keys:
                    if item[key] > max_values[key]["value"]:
                        max_values[key] = {"value": item[key], "Name": item["Name"]}

            # Convert the result into a list of dictionaries as specified
            result = [
                {
                    "Key": key,
                    "Max Value": max_values[key]["value"],
                    "Name": max_values[key]["Name"],
                }
                for key in max_values
            ]

            print(
                f"Finished fetching weekly report for guild with id {guild_id}. Compared stats of {len(summoners)} summoners."
            )
            return result
        else:
            print(f"No summoners found for guild with id {guild_id}.")
            return None
    else:
        print(f"Guild {guild_id} does not exist in the database")


# Fetch all matches stored for summer within a certain range
async def fetch_all_summoner_match_data_by_range(summoner_puuid, range=7):
    print(f"Fetching all matches for {summoner_puuid} within the last {range} days")
    collection = db.cached_match_data

    now = datetime.now(timezone.utc)
    lower_range = now - timedelta(days=range)
    lower_range_epoch = int(lower_range.timestamp() * 1000)

    collection.create_index([("summoner_puuid", 1)])
    collection.create_index([("info.gameStartTimestamp", 1)])

    query = {
        "summoner_puuid": summoner_puuid,
        "info.gameStartTimestamp": {"$gte": lower_range_epoch},
    }

    documents = collection.find(query)

    if not documents:
        print(
            f"No summoner match data found for {summoner_puuid} within the last {range} days."
        )
        return None
    else:
        return list(documents)
